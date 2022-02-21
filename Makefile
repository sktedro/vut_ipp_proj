TESTSDIR=../ipp_2022_fan-made-tests
JEXAMDIR=../jexamxml


test_parser:
	php8.1 test.php --directory="$(TESTSDIR)/parse-only/" --recursive --parse-only --jexampath="$(JEXAMDIR)" > report.html

test_interpret:
	php8.1 test.php --directory="$(TESTSDIR)/interpret-only/" --recursive --int-only --jexampath="$(JEXAMDIR)" > report.html

test:
	php8.1 test.php --directory="$(TESTSDIR)" --recursive --jexampath="$(JEXAMDIR)" > report.html
