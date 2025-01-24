# Bank of America PDF statements parser
## Description
The script parses single pdf statement or all pdf statements in the directory to csv files grouped by `account number` and `section`

## Features
* Supports both single account statements and combibed account statements when one pdf has multiple accounts embedded
* Extracts all transaction information including multiline transaction. That's something not supported by services like CreditKarma
* Detects all sections from the statement such as `Checks`, `Deposits and other additions` etc

## Usage
When parsed statements csv files are named as `<accountnumber>_<section>.csv`. Eg:
```
5672_ATM and debit card subtractions.csv
5672_Checks.csv
5672_Deposits and other additions.csv
5672_Other subtractions.csv
5672_Service fees.csv
``` 

Script assumes that statement named same way as downloaded from the site. Eg: `eStmt_2017-08-23.pdf`

### Parse all statements in the folder
Will parse all the statements in `~/data/checking` and put output into `~/data/out`
`python main.py --dir "~/data/checking" --out_dir "~/data/out"`



### Parse Single statement
`python main.py --statement "~/data/checking/eStmt_2017-08-23.pdf" --out_dir "~/data/out"`