TESTSDIR=../ipp_2022_fan-made-tests
JEXAMDIR=../jexamxml
TEST=../ipp_2022_fan-made-tests/interpret-only/xml_structure/xml_fromat2


test_parser:
	@echo "Testing the parser"
	@php8.1 test.php --directory="$(TESTSDIR)/parse-only/" --recursive --parse-only --jexampath="$(JEXAMDIR)" > report.html; cat report.html | grep -e "Passed\|Congratulations"; echo
	@# php8.1 test.php --directory="$(TESTSDIR)/parse-only/" --recursive --parse-only --jexampath="$(JEXAMDIR)" > report.html; google-chrome report.html &

test_interpret:
	@echo "Testing the interpret"
	@php8.1 test.php --directory="$(TESTSDIR)/interpret-only/" --recursive --int-only --jexampath="$(JEXAMDIR)" > report.html; cat report.html | grep -e "Passed\|Congratulations"; echo
	@# php8.1 test.php --directory="$(TESTSDIR)/interpret-only/" --recursive --int-only --jexampath="$(JEXAMDIR)" > report.html; google-chrome report.html &

test_both: 
	@echo "Testing both the parser and the interpret"
	@ php8.1 test.php --directory="$(TESTSDIR)/both/" --recursive --jexampath="$(JEXAMDIR)" > report.html; cat report.html | grep -e "Passed\|Congratulations"; echo
	@# php8.1 test.php --directory="$(TESTSDIR)/both/read/" --recursive --jexampath="$(JEXAMDIR)" > report.html; cat report.html | grep -e "Passed\|Congratulations"; echo

test: test_parser test_interpret test_both
	rm report.html



# TODO
pack:
	zip xskalo01.zip parse.php test.php interpret.py

clean:
	rm report.html

tmp:
	python3 interpret.py --source="$(TEST).src" --input="$(TEST).in"; echo "Finished with $$?"; echo
