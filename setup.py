from setuptools import setup

with open('README.md', 'r') as fh:
  long_description = fh.read()
setup(
  name = 'spychronous',
  py_modules = ['spychronous'],
  package_dir={'':'src'},
  version = '1.0.post3',
  license='MIT',
  description = 'A simple synchronous job runner for parallel processing tasks in Python.',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  author = 'Santiago C Paredes',
  author_email = 'santiago.paredes2012@gmail.com',
  url = 'https://github.com/scparedes/spychronous',
  download_url = 'https://github.com/scparedes/spychronous/releases/download/1.0.post3/spychronous-1.0.post3.tar.gz',
  keywords = ['multiprocessing', 'multiprocess', 'multi', 'process', 'synchronous', 'job', 'runner'],
  install_requires=[
  ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
  ],
)