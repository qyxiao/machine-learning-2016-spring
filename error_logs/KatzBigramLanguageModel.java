package nlp.assignments;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import nlp.langmodel.LanguageModel;
import nlp.util.Counter;
import nlp.util.CounterMap;

/**
 * A dummy language model -- uses empirical unigram counts, plus a single
 * ficticious count for unknown words.
 */
class KatzBigramLanguageModel implements LanguageModel {

	static final String START = "<S>";
	static final String STOP = "</S>";
	static final String UNKNOWN = "*UNKNOWN*";
	static final int cutOff = 5;

	Counter<String> wordCounter = new Counter<String>();
	CounterMap<String, String> bigramCounter = new CounterMap<String, String>();
	Counter<String> probabilities = new Counter<String>();
	Counter<String> backoffs = new Counter<String>();
	Counter<String> discountedWordCounter = new Counter<String>();
	Counter<String> discountedBigramCounter = new Counter<String>();

	public double getBigramProbability(String previousWord, String word) {
		double bigramProbability = probabilities.getCount(previousWord + " "
				+ word);
		if (Double.isNaN(bigramProbability)
				|| Double.isInfinite(bigramProbability)
				|| bigramProbability < 0)
			System.err.println("stop");

		if (bigramProbability != 0)
			return bigramProbability;

		double unigramProbability = probabilities.getCount(word);
		if (unigramProbability == 0) {
			// System.out.println("UNKNOWN Word: " + word);
			unigramProbability = probabilities.getCount(UNKNOWN);
		}
		if (Double.isNaN(unigramProbability)
				|| Double.isInfinite(unigramProbability)
				|| unigramProbability < 0)
			System.err.println("stop");

		double backoff = backoffs.getCount(previousWord);
		if (backoff == 0) {
			if (probabilities.getCount(previousWord) == 0)
				backoff = 1.0;
		}
		return unigramProbability * backoff;
	}

	public double getSentenceProbability(List<String> sentence) {
		List<String> stoppedSentence = new ArrayList<String>(sentence);
		stoppedSentence.add(0, START);
		stoppedSentence.add(STOP);
		double probability = 1.0;
		String previousWord = stoppedSentence.get(0);
		for (int i = 1; i < stoppedSentence.size(); i++) {
			String word = stoppedSentence.get(i);
			probability *= getBigramProbability(previousWord, word);
			previousWord = word;
		}
		return probability;
	}

	String generateWord() {
		double sample = Math.random();
		double sum = 0.0;
		for (String word : wordCounter.keySet()) {
			sum += wordCounter.getCount(word);
			if (sum > sample) {
				return word;
			}
		}
		return UNKNOWN;
	}

	public List<String> generateSentence() {
		List<String> sentence = new ArrayList<String>();
		String word = generateWord();
		while (!word.equals(STOP)) {
			sentence.add(word);
			word = generateWord();
		}
		return sentence;
	}

	public KatzBigramLanguageModel(Collection<List<String>> sentenceCollection) {
		for (List<String> sentence : sentenceCollection) {
			List<String> stoppedSentence = new ArrayList<String>(sentence);
			stoppedSentence.add(0, START);
			stoppedSentence.add(STOP);
			String previousWord = stoppedSentence.get(0);
			for (int i = 1; i < stoppedSentence.size(); i++) {
				String word = stoppedSentence.get(i);
				wordCounter.incrementCount(word, 1.0);
				discountedWordCounter.incrementCount(word, 1.0);
				discountedBigramCounter.incrementCount(previousWord + " "
						+ word, 1.0);
				bigramCounter.incrementCount(previousWord, word, 1.0);
				previousWord = word;
			}
		}
		normalizeDistributions();
	}

	private void normalizeDistributions() {
		double[] unigramBuckets = new double[cutOff + 2];
		for (String word : wordCounter.keySet()) {
			double count = wordCounter.getCount(word);
			if (count <= cutOff + 1)
				unigramBuckets[(int) count]++;
		}

		double[] bigramBuckets = new double[cutOff + 2];
		for (String previousWord : bigramCounter.keySet()) {
			Counter<String> currentCounter = bigramCounter
					.getCounter(previousWord);
			for (String word : currentCounter.keySet()) {
				double count = currentCounter.getCount(word);
				if (count <= cutOff + 1)
					bigramBuckets[(int) count]++;
			}
		}

		double normalizer = 1.0 / wordCounter.totalCount();
		double A = (cutOff + 1) * unigramBuckets[cutOff + 1]
				/ unigramBuckets[1];
		for (String word : wordCounter.keySet()) {
			double count = wordCounter.getCount(word);
			if (count > cutOff)
				probabilities.setCount(word, count * normalizer);
			else {
				double discountedCount = (count + 1)
						* unigramBuckets[(int) count + 1]
						/ unigramBuckets[(int) count];
				double probability = count * normalizer
						* (discountedCount / count - A) / (1 - A);
				probabilities.setCount(word, probability);
				if (Double.isNaN(probability) || Double.isInfinite(probability)
						|| probability < 0)
					System.err.println("stop");
			}
		}
		probabilities.setCount(UNKNOWN, unigramBuckets[1] * normalizer
				/ wordCounter.size());

		A = (cutOff + 1) * bigramBuckets[cutOff + 1] / bigramBuckets[1];
		Counter<String> forwardProbability = new Counter<String>();
		Counter<String> backwardProbability = new Counter<String>();
		for (String previousWord : bigramCounter.keySet()) {
			Counter<String> currentCounter = bigramCounter
					.getCounter(previousWord);
			normalizer = 1.0 / currentCounter.totalCount();
			double probability = 0;
			double probabilitySoFar = 0;
			for (String word : currentCounter.keySet()) {
				double count = currentCounter.getCount(word);
				if (count > cutOff) {
					probability = count * normalizer;
					// probability *= 0.99;
				} else {
					double discountedCount = (count + 1)
							* bigramBuckets[(int) count + 1]
							/ bigramBuckets[(int) count];
					probability = count * normalizer
							* (discountedCount / count - A) / (1 - A);
				}
				if (Double.isNaN(probability) || Double.isInfinite(probability)
						|| probability < 0)
					System.err.println("stop");
				probabilities.setCount(previousWord + " " + word, probability);
				backwardProbability.incrementCount(previousWord,
						probabilities.getCount(word));
				probabilitySoFar += probability;
			}
			forwardProbability.setCount(previousWord, probabilitySoFar);
		}

		for (String word : wordCounter.keySet()) {
			double backoff = (1.0 - forwardProbability.getCount(word))
					/ (1.0 - backwardProbability.getCount(word));
			if (Double.isNaN(backoff) || Double.isInfinite(backoff)
					|| backoff == 0)
				System.err.println("stop");
			backoffs.setCount(word, backoff);
		}
	}
}
