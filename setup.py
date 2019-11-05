
import setuptools

with open('README.rst', 'r', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='hnr_downloader',
    version='1.0.0.001',
    description='A download manager by Python.',
    long_description=long_description,
    url='https://github.com/dergenlee/hnr_downloader',
    author='Dergen Lee',
    author_email='dergenlee@163.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8'
    ],
    keywords='download manager',
    platforms=[],
    project_urls={
        'Documentation': 'https://github.com/dergenlee/hnr_downloader',
        'Funding': 'https://donate.pypi.org',
        'Source': 'https://github.com/dergenlee/hnr_downloader',
        'Tracker': 'https://github.com/dergenlee/hnr_downloader/issues',
    },
    packages=setuptools.find_packages(),
    install_requires=[
        'wxPython>=4.0.6',
        'requests>=2.22.0'],
    python_requires='>=3',
    package_data={
        '': ['*.json', 
            'locale/*/LC_MESSAGES/*.*']
    },
    entry_points={
        'console_scripts': ['hnr_dl = hnr_downloader.main:start']
    }
)
