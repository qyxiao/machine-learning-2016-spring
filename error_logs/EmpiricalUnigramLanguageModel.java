package nlp.assignments;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import nlp.langmodel.LanguageModel;
import nlp.util.Counter;

/**
 * A dummy language model -- uses empirical unigram counts, plus a single
 * ficticious count for unknown words.
 */
class EmpiricalUnigramLanguageModel implements LanguageModel {

	static final String STOP = "</S>";
	static final String UNKNOWN = "*UNKNOWN*";

	Counter<String> wordCounter = new Counter<String>();

	public double getWordProbability(List<String> sentence, int index) {
		String word = sentence.get(index);
		double count = wordCounter.getCount(word);
		if (count == 0) {
			return wordCounter.getCount(UNKNOWN);
		}
		return count;
	}

	public double getSentenceProbability(List<String> sentence) {
		List<String> stoppedSentence = new ArrayList<String>(sentence);
		stoppedSentence.add(STOP);
		double probability = 1.0;
		for (int index = 0; index < stoppedSentence.size(); index++) {
			probability *= getWordProbability(stoppedSentence, index);
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

	public EmpiricalUnigramLanguageModel(
			Collection<List<String>> sentenceCollection) {
		for (List<String> sentence : sentenceCollection) {
			List<String> stoppedSentence = new ArrayList<String>(sentence);
			stoppedSentence.add(STOP);
			for (String word : stoppedSentence) {
				wordCounter.incrementCount(word, 1.0);
			}
		}
		wordCounter.incrementCount(UNKNOWN, 1.0);
		wordCounter.normalize();
	}
}
