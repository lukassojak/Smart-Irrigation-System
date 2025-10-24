import time
from smart_irrigation_system.server.core.server_core import IrrigationServer

def main():
    server = IrrigationServer(broker_host="localhost", broker_port=1883)
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop()

if __name__ == "__main__":
    main()
