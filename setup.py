try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='crochet',
    version='0.5',
    description="Asynchronous calls for threaded applications",
    install_requires=[
        "Twisted>=11.0",
        ],
    keywords="twisted threading",
    license="MIT",
    packages=["crochet"],
    url="https://github.com/itamarst/crochet",
    maintainer='Itamar Turner-Trauring',
    maintainer_email='itamar@futurefoundries.com',
    long_description=open('README.rst').read(),
)
