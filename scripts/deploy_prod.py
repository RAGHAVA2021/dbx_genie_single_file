from sales_genie.cli import main

raise SystemExit(main(["deploy-prod", *__import__("sys").argv[1:]]))
