import re
import collections
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf
import random

# for proper formatting
np.set_printoptions(linewidth = 1000000, suppress = True)

# hyperparameters
num_sentences = 100000
embed_dim = 100
glove_alpha = 0.75
glove_xmax = 100.0
glove_learning_rate = 0.05
glove_batch_size = 512
glove_training_epochs = 100

# data dir
sst_home = 'data5/training-data'

def load_sst_data(path):
    data = []
    with open(path) as f:
        for i, line in enumerate(f):
            example = {}
            example['text'] = line
            data.append(example)
            if i > num_sentences:
                break
    return data


def readEvalVocab(path):
    Vocab = []
    with open(path) as f:
        for i, line in enumerate(f):
            Vocab.append(line[:-1])
            print(line[:-1])
    return Vocab

evalVocab = readEvalVocab(sst_home + '/evalVocab.txt')
training_set = load_sst_data(sst_home + '/training-data1m.txt')


def tokenize(string):
    return string.split()


word_counter = collections.Counter()
for example in training_set:
    word_counter.update(tokenize(example['text']))
    # print(tokenize(example['text']))
vocabulary = [pair[0] for pair in word_counter.most_common()]
index_to_word_map = dict(enumerate(vocabulary))
word_to_index_map = dict([(index_to_word_map[index], index) for index in index_to_word_map])


def extract_cooccurrences(dataset, word_map, amount_of_context=4):
    num_words = len(vocabulary)
    cooccurrences = np.zeros((num_words, num_words))
    nonzero_pairs = set()
    for example in dataset:
        words = tokenize(example['text'])
        for target_index in range(len(words)):
            target_word = words[target_index]
            if target_word not in word_to_index_map:
                continue
            target_word_index = word_to_index_map[target_word]
            min_context_index = max(0, target_index - amount_of_context)
            max_word = min(len(words), target_index + amount_of_context)
            for context_index in list(range(min_context_index, target_index)) + list(range(target_index + 1, max_word)):
                context_word = words[context_index]
                if context_word not in word_to_index_map:
                    continue
                context_word_index = word_to_index_map[context_word]
                cooccurrences[target_word_index][context_word_index] += 1.0
                nonzero_pairs.add((target_word_index, context_word_index))
    return cooccurrences, list(nonzero_pairs)


cooccurrences, nonzero_pairs = extract_cooccurrences(training_set, vocabulary)


def similarity(word_one, word_two):
    vec_one = model.get_embedding(word_to_index_map[word_one]).reshape(1, -1)
    vec_two = model.get_embedding(word_to_index_map[word_two]).reshape(1, -1)
    return float(cosine_similarity(vec_one, vec_two))

# a vanilla tester scoring function used in training phase
def score(model):
    score = 0
    score += similarity('a', 'an') > similarity('a', 'documentary')
    score += similarity('in', 'of') > similarity('in', 'picture')
    score += similarity('action', 'thriller') > similarity('action', 'end')
    score += similarity('films', 'movies') > similarity('films', 'almost')
    score += similarity('film', 'movie') > similarity('film', 'movies')
    score += similarity('watch', 'see') > similarity('watch', 'down')
    score += similarity('funny', 'entertaining') > similarity('funny', 'seems')
    score += similarity('good', 'great') > similarity('good', 'minutes')
    return score


class glove:
    def __init__(self, num_words):
        # Define the hyperparameters
        self.dim = embed_dim  # The size of the learned embeddings
        self.alpha = glove_alpha
        self.xmax = glove_xmax
        self.learning_rate = glove_learning_rate
        self.batch_size = glove_batch_size
        self.training_epochs = glove_training_epochs
        self.display_epoch_freq = 10  # How often to test and print out statistics
        self.num_words = num_words  # The number of vectors to learn
        self.embeddings_cache = None  # To be set later

        #self.inter_sess = tf.InteractiveSession();

        # Define the inputs to the model
        self.Wi_input = tf.placeholder(tf.int32, None)
        self.Wj_input = tf.placeholder(tf.int32, None)
        self.coocur_input = tf.placeholder(tf.float32, None)

        # Define the trainable parameters of the model
        self.embeddings = tf.Variable(tf.random_uniform([len(vocabulary), self.dim], 1.0, -1.0))
        self.bias = tf.Variable(tf.zeros([len(vocabulary)]))

        # Define the forward computation of the model
        self.Wi_embeddings = tf.reshape(tf.nn.embedding_lookup([self.embeddings], self.Wi_input),
                                        [self.batch_size, 1, self.dim ])
        # print(tf.shape(self.Wi_embeddings))
        self.Wj_embeddings = tf.reshape(tf.nn.embedding_lookup([self.embeddings], self.Wj_input),
                                        [self.batch_size, self.dim, 1])
        self.bi = tf.reshape(tf.nn.embedding_lookup([self.bias], self.Wi_input), [self.batch_size, 1])
        self.bj = tf.reshape(tf.nn.embedding_lookup([self.bias], self.Wj_input), [self.batch_size, 1])
        self.dot_products = tf.reshape(tf.batch_matmul(self.Wi_embeddings, self.Wj_embeddings), [self.batch_size, 1])
        # tf.Print(self.dot_products, [self.dot_products], message="This is a: ")
        self.square_term = tf.square(tf.add_n([self.dot_products, self.bi, self.bj,
                                               tf.neg(tf.log(tf.to_float(self.coocur_input)))]))
        self.weight_factor = tf.minimum(1.0, tf.pow(tf.div(self.coocur_input, self.xmax), self.alpha))
        self.example_cost = tf.mul(self.weight_factor, self.square_term)

        # Define the cost function
        self.total_cost = tf.reduce_mean(self.example_cost)

        # Train
        self.optimizer = tf.train.AdagradOptimizer(self.learning_rate).minimize(self.total_cost)

        # Initialize variables
        self.init = tf.initialize_all_variables()

        # Initialize the model
        self.sess = tf.Session()
        self.sess.run(self.init)

    def train(self, cooccurrences, nonzero_pairs, num_words):
        self.embeddings_cache = None
        print('Training...')

        for epoch in range(self.training_epochs):
            random.shuffle(nonzero_pairs)

            avg_cost = 0.0
            total_batches = int(len(nonzero_pairs) / self.batch_size)

            for i in range(total_batches):

                # Assemble a minibatch dictionary to feed to `sess.run()`
                i_input = [item[0] for item in nonzero_pairs[i * self.batch_size : (i + 1) * self.batch_size]]
                j_input = [item[1] for item in nonzero_pairs[i * self.batch_size : (i + 1) * self.batch_size]]

                coocur_input = cooccurrences[i_input, j_input].reshape(self.batch_size, 1)

                feed = {self.Wi_input: i_input,
                        self.Wj_input: j_input,
                        self.coocur_input: coocur_input}

                _, c = self.sess.run([self.optimizer, self.total_cost],
                                     feed_dict=feed)

                # Compute average loss
                avg_cost += c / total_batches

            # Display statistics at a frequency
            if (epoch + 1) % self.display_epoch_freq == 0:
                self.cache_embeddings()  # Make sure we run scoring with a fresh copy of the embeddings
                print("Epoch:", (epoch + 1), "Cost:", avg_cost, "Score:", score(self))

    # only cache embeddings when to show statistics for faster speed
    def cache_embeddings(self):
        self.embeddings_cache = self.sess.run(self.embeddings)

    def get_embedding(self, index):
        if self.embeddings_cache is None:
            self.cache_embeddings()
        return self.embeddings_cache[index, :]

    def output(self):
        if self.embeddings_cache is None:
            self.cache_embeddings()
        self.fout = open('gloveEmbed.txt', 'w')
        self.fout.write(str(len(evalVocab)) + ' ' + str(self.dim) + '\n')
        for vocab in evalVocab:
            self.fout.write(vocab)
            self.fout.write(' ')
            # print(np.array_str(self.get_embedding(word_to_index_map[vocab]))[1:-1])
            if vocab in word_to_index_map:
                self.fout.write(np.array_str(self.get_embedding(word_to_index_map[vocab]).reshape(1,-1))[2:-2])
            else:
                for i in range(self.dim):
                    self.fout.write('0.0' + ' ')
            self.fout.write('\n')


model = glove(len(vocabulary))

model.train(cooccurrences, nonzero_pairs, len(vocabulary))
model.output()
