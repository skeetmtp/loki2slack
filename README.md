# loki2slack


## init

```
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## run

```
python3 main.py
```

## build

```
pyinstaller main.py -y -F --clean -n "loki2slack"
```
