from setuptools import setup

setup(
    name='birbapi',
    version='0.1',
    description='Twitter API interface',
    long_description="A basic interface for the Twitter API. Supports Python 3, OAuth, paging.",
    author='Edmond Burnett',
    author_email='_@edmondburnett.com',
    url='https://github.com/edmondburnett/birbapi',
    license='MIT',
    packages=['birbapi'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)