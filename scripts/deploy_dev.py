from sales_genie.cli import main

raise SystemExit(main(["deploy-dev", *__import__("sys").argv[1:]]))
