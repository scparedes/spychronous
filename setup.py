from setuptools import setup, find_packages

version = '1.0.post4'

with open('README.md', 'r') as fh:
  long_description = fh.read()

setup(
  name = 'spychronous',
  py_modules = ['spychronous'],
  packages=find_packages('src'),
  package_dir={'':'src'},
  version = version,
  license='MIT',
  description = 'A simple synchronous job runner for parallel processing tasks in Python.',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  author = 'Santiago C Paredes',
  author_email = 'santiago.paredes2012@gmail.com',
  url = 'https://github.com/scparedes/spychronous',
  download_url = 'https://github.com/scparedes/spychronous/releases/download/%s/spychronous-%s.tar.gz' % (version, version),
  keywords = ['multiprocessing', 'multiprocess', 'multi', 'process', 'synchronous', 'job', 'runner', 'simple'],
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
