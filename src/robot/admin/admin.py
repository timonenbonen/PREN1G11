import input_handler
import output_handler
import communication

def main():
    print("Admin ready. Waiting for start...")

    # Placeholder until GPIO is hooked up
    if input_handler.wait_for_start_button():
        print("Starting run process...")

        route_status, path = communication.calculate_route()

        if route_status == "valid":
            communication.send_uart_command(f"DRIVE:{path}")
        else:
            communication.send_uart_command("TURN")
            output_handler.signal_error()

        output_handler.signal_arrival()

if __name__ == "__main__":
    main()