TESTSDIR=../ipp_2022_fan-made-tests
JEXAMDIR=../jexamxml
TEST=../ipp_2022_fan-made-tests/interpret-only/xml_structure/xml_fromat2


test_parser:
	php8.1 test.php --directory="$(TESTSDIR)/parse-only/" --recursive --parse-only --jexampath="$(JEXAMDIR)" > report.html; google-chrome report.html &

test_interpret:
	php8.1 test.php --directory="$(TESTSDIR)/interpret-only/" --recursive --int-only --jexampath="$(JEXAMDIR)" > report.html; cat report.html | grep -e "Passed\|Congratulations"; echo
# php8.1 test.php --directory="$(TESTSDIR)/interpret-only/" --recursive --int-only --jexampath="$(JEXAMDIR)" > report.html; google-chrome report.html &

test:
	php8.1 test.php --directory="$(TESTSDIR)" --recursive --jexampath="$(JEXAMDIR)" > report.html

# TODO
pack:
	zip xskalo01.zip parse.php test.php interpret.py

clean:
	rm *.html

tmp:
	python3 interpret.py --source="$(TEST).src" --input="$(TEST).in"; echo "Finished with $$?"; echo
