import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-ausleihe',
    version='0.1.3',
    packages=find_packages(),
    include_package_data=True,
    description='Django-App für die Ausleihe von Medien.',
    long_description=README,
    license='MIT License',
    url='https://github.com/hutchison/django-ausleihe',
    install_requires=[
        'Django>=3.0',
        'django-fsmedhro-core>=0.2.6',
    ],
    python_requires=">=3.6",
    author='Martin Darmüntzel',
    author_email='martin@trivialanalog.de',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
