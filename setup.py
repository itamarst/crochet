try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    name='crochet',
    version='0.8.1',
    description="Use Twisted from threaded applications",
    install_requires=[
        "Twisted>=11.1",
        ],
    keywords="twisted threading",
    license="MIT",
    packages=["crochet", "crochet.tests"],
    url="https://github.com/itamarst/crochet",
    maintainer='Itamar Turner-Trauring',
    maintainer_email='itamar@futurefoundries.com',
    long_description=open('README.rst').read(),
)
