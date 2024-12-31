cd content
python optimize.py
cd ..
hugo
rsync -av --delete ./public/ Dennis960:~/public/Blog