import docx
doc = docx.Document(r'c:\Users\Asus\OneDrive - VietNam National University - HCM INTERNATIONAL UNIVERSITY\Phan An Phu-ITITIU21280 - ReportThesis.docx')

with open(r'D:\ProjectThesis\dropout_prediction\thesis_content.txt', 'w', encoding='utf-8') as f:
    for i in range(408, 520):
        p = doc.paragraphs[i]
        text = p.text.strip()
        if text:
            f.write(f'--- {i} [{p.style.name}] ---\n')
            f.write(text + '\n')
print('Done')
