TESTSDIR=../ipp_2022_fan-made-tests
JEXAMDIR=../jexamxml

.PHONY: doc

# Only test the parser
test_parser:
	@ echo "Testing the parser"
	@ php8.1 test.php --directory="$(TESTSDIR)/parse-only/" --recursive    \
		--parse-only --jexampath="$(JEXAMDIR)" > report.html;          \
		cat report.html | grep -e "tests passed\|Congratulations"

# Only test the interpret
test_interpret:
	@ echo "Testing the interpret"
	@ php8.1 test.php --directory="$(TESTSDIR)/interpret-only/" --recursive\
		--int-only --jexampath="$(JEXAMDIR)" > report.html;            \
		cat report.html | grep -e "tests passed\|Congratulations"

# Test both of them at once (forward parser output to the interpret)
test_both: 
	@ echo "Testing both the parser and the interpret"
	@ php8.1 test.php --directory="$(TESTSDIR)/both/" --recursive          \
		--jexampath="$(JEXAMDIR)" > report.html;                       \
		cat report.html | grep -e "tests passed\|Congratulations"

# Test parser, interpret and then both of them
test: test_parser test_interpret test_both
	rm report.html

doc:
	$(MAKE) -C doc

pack: doc
	mv doc/doc.pdf ./
	zip xskalo01.zip parse.php test.php interpret.py doc.pdf

clean:
	rm -f *.html *.zip *.pdf
	$(MAKE) -C doc clean
