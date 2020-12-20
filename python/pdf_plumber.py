import pdfplumber
pdf = pdfplumber.open('../data/results.pdf')

for page in pdf.pages:
   # page = pdf.pages[0]
    text = page.extract_text()
    print(text)
pdf.close()

num_pages = len(pdf.pages)
print (f"num pages {num_pages}")