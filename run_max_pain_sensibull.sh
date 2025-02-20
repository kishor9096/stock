# filepath: /home/ubuntu/LLM/stock/run_max_pain_sensibull.sh
#!/bin/bash
source /home/ubuntu/LLM/stock/.venv/bin/activate
/home/ubuntu/LLM/stock/.venv/bin/python /home/ubuntu/LLM/stock/max_pain_sensibull.py >> /home/ubuntu/LLM/stock/max_pain_sensibull_cron_log.txt 2>&1

/home/ubuntu/LLM/stock/.venv/bin/python /home/ubuntu/LLM/stock/moneyControlScraping.py >> /home/ubuntu/LLM/stock/moneyControlScraping_cron_log.txt 2>&1
