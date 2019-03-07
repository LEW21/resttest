from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding = 'utf-8') as f:
	long_description = f.read()


setup(
    name = 'resttest',
    version = '0.1.0',
    description = "Framework for testing and documenting REST APIs",
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = "Linus Lewandowski",
    author_email = 'linus.lewandowski@netguru.co',
    url = 'https://github.com/LEW21/resttest/',

	classifiers = [
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Developers',
		'Topic :: Software Development :: Testing',
		'Topic :: Software Development :: Documentation',
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3 :: Only',
		'Programming Language :: Python :: 3.7',
	],
    keywords = "test docs rest http api",

    install_requires = [
        'requests',
        'redbaron',
    ],

    packages=find_packages(),

    zip_safe=True,
)
