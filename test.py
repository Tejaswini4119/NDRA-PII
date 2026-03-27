import spacy
from presidio_analyzer import AnalyzerEngine

nlp = spacy.load("en_core_web_sm")
analyzer = AnalyzerEngine()

text = "My name is John and my phone number is 9876543210"

results = analyzer.analyze(text=text, language="en")

print(results)
