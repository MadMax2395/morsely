# morsely
A python library to translate morse &lt;-> alphanumeric.

## Encoder
TODO

## Decoder
TODO

## Installation
With anaconda or miniconda installed, execute:
```
conda create --name py_m_env python=3.11
```

### Windows
```
conda activate py_m_env
```

### Linux/MacOS
```
source activate py_m_env
```

Then, execute:

```
pip install numpy==2.2.3
pip install scipy==1.15.1
```

## Execute tests
execute:
```
pip install pytest==8.3.5
pip install coverage==7.6.12
coverage run -m pytest tests/ && coverage report -m
```

## Distribution PyPi
```
pip install twine==6.1.0
python setup.py sdist bdist_wheel
pip install dist/morsely-0.0.x-py3-none-any.whl

twine upload --repository testpypi dist/*
twine upload dist/*
```