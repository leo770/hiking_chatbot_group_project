PU usage percentage
CPU_USAGE=$(top -b -n 1 | grep "Cpu(s)" | awk '{print $2}' | awk -F. '{print $1}')

# Get memory usage percentage
MEMORY_USAGE=$(free | awk '/Mem/{printf("%.2f"), $3/$2*100}')

# Get network usage percentage
NETWORK_USAGE=$(cat /proc/net/dev | grep 'eth0:' | awk '{print $2}' | awk -F: '{print $1}')

# Check if CPU, memory, or network usage is greater than 80%
if [ $CPU_USAGE -gt 80 ] || [ $(echo "$MEMORY_USAGE > 80" | bc) -eq 1 ] || [ $NETWORK_USAGE -gt 80 ]; then
	docker service update --replicas 4 hiking_chatbot
else
	docker service update --replicas 2 hiking_chatbot
fi
