<div id="top"></div>

<!-- PROJECT LOGO -->
<br />
<div align="center">

  <h1 align="center">Darkweb markets Crawler</h1>

  <p align="center">
    Crawler to obtain data from the Dark Web marketplaces in order to get some databases for further analysis. 
    asd
    <br /> <br/>
    <br />
    <a href="https://github.com/vicviclablab/darkmarkets_crawler/src">Code</a>
    ·
    <a href="https://github.com/vicviclablab/darkmarkets_crawler/src/markets">Markets code</a>
    ·
    <a href="https://github.com/vicviclablab/darkmarkets_crawler/src/analysis">Analysis code</a>
  </p>
</div>

##

<!-- TABLE OF CONTENTS -->
  <h3> Table of Contents </h3>
  <ol>
    <li><a href="#about-the-project">About The Project</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>


<!-- ABOUT THE PROJECT -->
## About The Project

Currently, the Dark Web is one key platform for the online trading of illegal products and services. Analysing the .onion sites hosting marketplaces is of interest for law enforcement and security researchers. This paper presents a study on 123k listings obtained from 6 different Dark Web markets. While most of current works leverage existing datasets, these are outdated and might not contain new products, e.g., those related to the 2020 COVID pandemic. Thus, we build a custom focused crawler to collect the data. Being able to conduct analyses on current data is of considerable importance as these marketplaces continue to change and grow, both in terms of products offered and users. Also, there are several anti-crawling mechanisms being improved, making this task more difficult and, consequently, reducing the amount of data obtained in recent years on these marketplaces. We conduct a data analysis evaluating multiple characteristics regarding the products, sellers, and markets. These characteristics include, among others, the number of sales, existing categories in the markets, the origin of the products and the sellers. Our study sheds light on the products and services being offered in these markets nowadays.

Moreover, we have conducted a case study on one particular productive and dynamic drug market, i.e., Cannazon. Our initial goal was to understand its evolution over time, analyzing the variation of products in stock and their price longitudinally. We realized, though, that during the period of study the market suffered a DDoS attack which damaged its reputation and affected users' trust on it, which was a potential reason which lead to the subsequent closure of the market by its operators. 

Consequently, our study provides insights regarding the last days of operation of such a productive market, and showcases the effectiveness of a potential intervention approach by means of disrupting the service and fostering mistrust.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

In order to use this tool, it is necessary to have installed the Tor browser, Python and some libraries such as Selenium (to be able to scrape the websites of the markets) and sqlite3 to be able to store the information obtained in a SQLite database.

### Prerequisites
1. Installing Tor
```sh
  sudo add-apt-repository ppa:micahflee/ppa
  sudo apt update 
  sudo apt install torbrowser-launcher
```
2. Installing Python
```sh
  sudo apt install python3
```

### Installation
1. Clone the repo
   ```sh
   git clone https://github.com/vicviclablab/darkmarkets_crawler
   ```
2. Install dependencies and libraries
  ```sh
   sudo pip3 install -r requirements.txt
   ```

### Execution
  ```sh
   python3 crawler.py market_name port file.txt
   ```
   Where the market_name is the market to crawl
   The port is the port that the crawl will use to connect through Tor to the market
   The file.txt is the file where the URLs will be stored for later analysis.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

- [x] Generic crawler structure
- [x] Create logs for crawler
- [x] Create specific markets crawler
- [x] Create option to parallelize processes
- [x] Create scripts in order to organize data from databases
- [ ] Crawl new markets
- [ ] Integrate free automatic CAPTCHA solvers
- [ ] Automatization
    - [ ] Automatic check for completeness of data crawled
    - [ ] Crawler automatically resume upon crashes
- [ ] Integrate AI module to crawl any new market based on the markets already viewed 


<p align="right">(<a href="#top">back to top</a>)</p>


<!-- CONTACT -->
## Contact

Víctor Labrador - victorlabrador10@gmail.com

<p align="right">(<a href="#top">back to top</a>)</p>


