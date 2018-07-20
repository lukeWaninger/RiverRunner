cd D:\OneDrive\git\RiverRunner
cp .\riverrunner\daily.py .

conda activate rr
python daily.py > .\riverrunner\data\logs\daily.txt

rm .\riverrunner\daily.py