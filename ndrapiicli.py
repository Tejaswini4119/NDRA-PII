import sys
import os
import requests
import json
from config.settings import settings

# This script assumes the server is NOT running, but uses the agents directly for now,
# OR we can make it a client that calls the API. 
# Let's make it Direct Agent use for simplicity, or API client?
# The request was "keep booth, test case and real upload use".
# Let's make this an Agent Interface wrapper.

sys.path.append(os.path.abspath("."))
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from agents.extractor import ExtractorAgent
from agents.classifier import ClassifierAgent
from agents.fusion_agent import FusionAgent
from agents.policy_agent import PolicyAgent
from agents.redaction_agent import RedactionAgent

def run_interactive():
    print("="*60)
    print(" NDRA-PII Interactive CLI ")
    print("="*60)
    
    extractor = ExtractorAgent()
    classifier = ClassifierAgent()
    fusion_agent = FusionAgent()
    policy_agent = PolicyAgent()
    redaction_agent = RedactionAgent()
    
    while True:
        try:
           file_path = input("\nEnter file path (or 'q' to quit): ").strip()
           if file_path.lower() == 'q':
               break
               
           # Remove quotes if user copied path with quotes
           file_path = file_path.replace('"', '').replace("'", "")
           
           if not os.path.exists(file_path):
               print(f"[ERROR] File not found: {file_path}")
               continue
               
           print(f"\n[1] Processing: {os.path.basename(file_path)}...")
           
           # Extract
           chunks = extractor.process(file_path)
           print(f"[OK] Extracted {len(chunks)} chunks.")
           
           # Classify
           pii_count = 0
           full_redacted_text = []
           print(f"[2] Analyzing for PII...")
           
           for chunk in chunks:
               classified = classifier.process(chunk)
               
               # Fusion
               classified = fusion_agent.fuse_chunk(classified)
               
               # Policy
               governed = policy_agent.evaluate_chunk(classified, trace_id="cli_trace")
               
               # Redaction
               final_chunk = redaction_agent.redact(governed)
               full_redacted_text.append(final_chunk.redacted_text)
               
               if final_chunk.detected_entities:
                   pii_count += len(final_chunk.detected_entities)
                   
                   # Print Decision
                   if final_chunk.decision.action != "Allow" or final_chunk.decision.risk_score > 0:
                        print(f"    [POLICY] Action: {final_chunk.decision.action} | Risk: {final_chunk.decision.risk_score}")
                        for trace in final_chunk.decision.justification_trace:
                            print(f"      - {trace}")
                        
                        # Show snippet of redacted text if Redacted
                        if final_chunk.decision.action == "Redact":
                            snippet = final_chunk.redacted_text[:100].replace("\n", " ") + "..."
                            print(f"    [REDACTED PREVIEW] {snippet}")

                   for pii in final_chunk.detected_entities:
                        loc = f"Page {pii.location.page_number} [{pii.location.char_start_on_page}:{pii.location.char_end_on_page}]" if pii.location else ""
                        safe_text = pii.text_value.encode('ascii', 'ignore').decode('ascii')
                        
                        # If redacted, mask the display here too
                        if final_chunk.decision.action == "Redact":
                            safe_text = f"[{pii.entity_type}]"
                            
                        print(f"    -> [{pii.entity_type}] '{safe_text}' (Score: {pii.score:.2f}) @ {loc}")
           
           print(f"\n[DONE] Found {pii_count} PII entities.")
           
           # Save Redacted File (PDF)
           if pii_count > 0:
               # 1. Prepare Output Dir
               output_dir = "output"
               os.makedirs(output_dir, exist_ok=True)
               
               base_name = os.path.basename(file_path)
               name, ext = os.path.splitext(base_name)
               out_file = os.path.join(output_dir, f"{name}_redacted.pdf")
               
               print(f"\n[3] Generating Redacted PDF: {out_file}")
               
               # 2. Build PDF
               try:
                   doc = SimpleDocTemplate(out_file, pagesize=letter)
                   styles = getSampleStyleSheet()
                   story = []
                   
                   # Add Title
                   title = Paragraph(f"Redacted Document: {base_name}", styles["Title"])
                   story.append(title)
                   story.append(Spacer(1, 12))
                   
                   # Add Content
                   # We join chunks, but better to add them as separate paragraphs to preserve some structure
                   for text_chunk in full_redacted_text:
                       # Handle newlines by replacing with <br/> for HTML-like flow in Paragraph
                       formatted_text = text_chunk.replace("\n", "<br/>")
                       
                       # We can also highlight redacted parts in red? 
                       # For now, just black text.
                       # If we want to highlight [REDACTED], we'd need regex to wrap it in <font color=red>...
                       
                       # Let's highlight entity tags like [PERSON] in Red color for visibility
                       import re
                       formatted_text = re.sub(r"(\[[A-Z_]+\])", r'<font color="red"><b>\1</b></font>', formatted_text)
                       
                       p = Paragraph(formatted_text, styles["BodyText"])
                       story.append(p)
                       story.append(Spacer(1, 12))
                       
                   doc.build(story)
                   print(f"[SUCCESS] Redacted PDF generated: {os.path.abspath(out_file)}")
                   
               except Exception as pdf_err:
                   print(f"[ERROR] Failed to generate PDF: {pdf_err}")
           
        except Exception as e:
            print(f"[ERROR] processing file: {e}")

if __name__ == "__main__":
    run_interactive()
