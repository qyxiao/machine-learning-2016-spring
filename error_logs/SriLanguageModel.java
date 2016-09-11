package nlp.assignments;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import nlp.langmodel.LanguageModel;
import nlp.util.Counter;

/**
 * A dummy language model -- uses empirical unigram counts, plus a single
 * fictitious count for unknown words.
 */
class SriLanguageModel implements LanguageModel {

	static final String START = "<s>";
	static final String STOP = "</s>";
	static final String UNKNOWN = "<unk>";

	Counter<String> probabilities = new Counter<String>();
	Counter<String> backoffs = new Counter<String>();

	public double getTrigramProbability(String prePreviousWord,
			String previousWord, String word) {
		double trigramProbability = probabilities.getCount(prePreviousWord
				+ " " + previousWord + " " + word);
		if (trigramProbability != 0)
			return Math.exp(trigramProbability);

		double bigramProbability = probabilities.getCount(previousWord + " "
				+ word);
		if (bigramProbability != 0)
			return Math.exp(bigramProbability
					+ backoffs.getCount(prePreviousWord + " " + previousWord));

		double unigramProbability = probabilities.getCount(word);
		if (unigramProbability == 0) {
			System.out.println("UNKNOWN Word: " + word);
			unigramProbability = probabilities.getCount(UNKNOWN);
		}
		return Math.exp(unigramProbability + backoffs.getCount(previousWord));
	}

	public double getSentenceProbability(List<String> sentence) {
		List<String> stoppedSentence = new ArrayList<String>(sentence);
		stoppedSentence.add(0, START);
		stoppedSentence.add(0, START);
		stoppedSentence.add(STOP);
		double probability = 1.0;
		String prePreviousWord = stoppedSentence.get(0);
		String previousWord = stoppedSentence.get(1);
		for (int i = 2; i < stoppedSentence.size(); i++) {
			String word = stoppedSentence.get(i);
			probability *= getTrigramProbability(prePreviousWord, previousWord,
					word);
			prePreviousWord = previousWord;
			previousWord = word;
		}
		if (probability == 0)
			System.err.println("Underflow");
		return probability;
	}

	String generateWord() {
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

	public SriLanguageModel(String fileName) {
		BufferedReader reader;
		try {
			reader = new BufferedReader(new FileReader(fileName));
			String line = reader.readLine();
			while (line != null) {
				if (!line.isEmpty() && line.charAt(0) == '-') {
					String[] parts = line.split("\t");
					if (parts.length != 2 && parts.length != 3) {
						System.err.println("BUG: " + Arrays.toString(parts));
					}
					probabilities.setCount(parts[1],
							Double.parseDouble(parts[0]) / Math.log10(Math.E));
					if (parts.length == 3) {
						backoffs.setCount(
								parts[1],
								Double.parseDouble(parts[2])
										/ Math.log10(Math.E));
					}
				}
				line = reader.readLine();
			}
		} catch (Exception e) {
			e.printStackTrace();
		}

	}

}
