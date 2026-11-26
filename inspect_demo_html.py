import os, glob

sample = glob.glob('D:/app/brag-lead-hunter/demos/*/index.html')[:5]
print("Demo samples:", sample)
if sample:
    with open(sample[0], 'r', encoding='utf-8') as f:
        print("First 500 chars of demo:", f.read()[:500])
