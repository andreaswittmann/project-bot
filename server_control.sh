#!/bin/bash

# Server Control Script for bewerbungs-bot
# Checks for running servers and provides start/restart functionality

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if Python server is running
check_python_server() {
    if pgrep -f "python.*server_enhanced.py" > /dev/null; then
        echo -e "${GREEN}✓ Python server (server_enhanced.py) is running${NC}"
        echo -e "  ${BLUE}📊 API:${NC} http://localhost:8002/api/v1/"
        echo -e "  ${BLUE}🔧 Health:${NC} http://localhost:8002/api/v1/health"
        echo -e "  ${BLUE}🌐 Frontend:${NC} http://localhost:8002/ (when built)"
        return 0
    else
        echo -e "${RED}✗ Python server (server_enhanced.py) is not running${NC}"
        echo -e "  ${YELLOW}📊 API:${NC} http://localhost:8002/api/v1/ (when started)"
        return 1
    fi
}

# Function to check if frontend dev server is running
check_frontend_server() {
    if pgrep -f "npm.*run dev" > /dev/null; then
        echo -e "${GREEN}✓ Frontend dev server (npm run dev) is running${NC}"
        echo -e "  ${BLUE}🌐 Frontend:${NC} http://localhost:3000/"
        echo -e "  ${BLUE}📊 API Proxy:${NC} http://localhost:3000/api/ → http://localhost:8002/api/"
        return 0
    else
        echo -e "${RED}✗ Frontend dev server (npm run dev) is not running${NC}"
        echo -e "  ${YELLOW}🌐 Frontend:${NC} http://localhost:3000/ (when started)"
        return 1
    fi
}

# Function to start Python server
start_python_server() {
    echo -e "${BLUE}Starting Python server...${NC}"
    nohup python server_enhanced.py > server.log 2>&1 &
    sleep 2
    if check_python_server > /dev/null; then
        echo -e "${GREEN}Python server started successfully${NC}"
    else
        echo -e "${RED}Failed to start Python server${NC}"
    fi
}

# Function to start frontend dev server
start_frontend_server() {
    echo -e "${BLUE}Starting frontend dev server...${NC}"
    cd frontend
    nohup npm run dev > ../frontend.log 2>&1 &
    cd ..
    sleep 3
    if check_frontend_server > /dev/null; then
        echo -e "${GREEN}Frontend dev server started successfully${NC}"
    else
        echo -e "${RED}Failed to start frontend dev server${NC}"
    fi
}

# Function to restart Python server
restart_python_server() {
    echo -e "${YELLOW}Restarting Python server...${NC}"
    pkill -f "python.*server_enhanced.py"
    sleep 1
    start_python_server
}

# Function to stop Python server
stop_python_server() {
    echo -e "${YELLOW}Stopping Python server...${NC}"
    pkill -f "python.*server_enhanced.py"
    sleep 1
    if ! pgrep -f "python.*server_enhanced.py" > /dev/null; then
        echo -e "${GREEN}Python server stopped successfully${NC}"
    else
        echo -e "${RED}Failed to stop Python server${NC}"
    fi
}

# Function to restart frontend server
restart_frontend_server() {
    echo -e "${YELLOW}Restarting frontend dev server...${NC}"
    pkill -f "npm.*run dev"
    sleep 1
    start_frontend_server
}

# Function to stop frontend server
stop_frontend_server() {
    echo -e "${YELLOW}Stopping frontend dev server...${NC}"

    # Kill all related frontend processes
    pkill -f "npm.*run dev"
    pkill -f "vite"
    pkill -f "esbuild.*--service"
    sleep 2

    # Check if any frontend processes are still running
    if ! pgrep -f "npm.*run dev" > /dev/null && ! pgrep -f "vite" > /dev/null; then
        echo -e "${GREEN}Frontend dev server stopped successfully${NC}"
    else
        echo -e "${RED}Failed to stop frontend dev server${NC}"
        echo -e "${YELLOW}Some processes may still be running. Try manual cleanup if needed.${NC}"
    fi
}

# Main function
main() {
    echo -e "${BLUE}=== Server Status Check ===${NC}"
    check_python_server
    check_frontend_server
    echo

    echo -e "${BLUE}=== Available Commands ===${NC}"
    echo "start-python    - Start Python server"
    echo "start-frontend  - Start frontend dev server"
    echo "restart-python  - Restart Python server"
    echo "restart-frontend- Restart frontend dev server"
    echo "stop-python     - Stop Python server"
    echo "stop-frontend   - Stop frontend dev server"
    echo "start-all       - Start both servers"
    echo "restart-all     - Restart both servers"
    echo "stop-all        - Stop both servers"
    echo "status          - Show current status"
    echo "quit            - Exit script"
    echo

    if [ $# -eq 0 ]; then
        echo -e "${YELLOW}Enter command:${NC}"
        read command
    else
        command=$1
    fi

    case $command in
        "start-python")
            start_python_server
            ;;
        "start-frontend")
            start_frontend_server
            ;;
        "restart-python")
            restart_python_server
            ;;
        "restart-frontend")
            restart_frontend_server
            ;;
        "stop-python")
            stop_python_server
            ;;
        "stop-frontend")
            stop_frontend_server
            ;;
        "start-all")
            start_python_server
            start_frontend_server
            ;;
        "restart-all")
            restart_python_server
            restart_frontend_server
            ;;
        "stop-all")
            stop_python_server
            stop_frontend_server
            ;;
        "status")
            echo -e "${BLUE}=== Server URLs ===${NC}"
            check_python_server
            echo
            check_frontend_server
            ;;
        "quit")
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid command. Use one of the commands listed above.${NC}"
            ;;
    esac
}

# Run main function with all arguments
main "$@"