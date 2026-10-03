from sales_genie.cli import main

raise SystemExit(main(["compare-dev-prod", *__import__("sys").argv[1:]]))
