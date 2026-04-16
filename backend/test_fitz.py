import fitz
doc = fitz.open()
doc.new_page()
print("hasattr write:", hasattr(doc, 'write'))
try:
    print("write type:", type(doc.write()))
except Exception as e:
    print("write error:", e)
try:
    print("tobytes type:", type(doc.tobytes()))
except Exception as e:
    print("tobytes error:", e)
