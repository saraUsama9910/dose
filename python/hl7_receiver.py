# جهاز الاستقبال - hl7_receiver.py
import socket

def start_hl7_receiver(ip="127.0.0.1", port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((ip, port))
        server.listen()
        print(f"Listening for HL7 messages on {ip}:{port}...")

        while True:
            client, addr = server.accept()
            with client:
                print(f"Connection from {addr}")
                message = client.recv(4096).decode("utf-8")
                print("\n----- HL7 Message Received -----\n")
                print(message)
                print("\n-------------------------------\n")

if __name__ == "__main__":
    start_hl7_receiver(port=5000)  # خلي البورت يطابق اللي هتكتبيه في جهازك
