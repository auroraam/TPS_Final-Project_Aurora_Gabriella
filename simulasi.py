import pygame
import random
import queue

# Ukuran layar
screen_width = 1000
screen_height = 600
customer_speed = 2
customer_size = (30, 30)
cashier_size = (50, 50)
gelato_size = (50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

exit_position = (1000, 600)

class Customer:
    def __init__(me, arrival_time, items):
        me.arrival_time = arrival_time # waktu memasuki antrian pembayaran
        me.items = items
        me.position = (random.randint(0, screen_width - customer_size[0]), 0)  # posisi dibagian atas layar
        me.pay_position = None
        me.gel_position = None
        me.exiting = False
        me.getting_gelato = False
        me.service_start_time = None
        me.departure_time = None # waktu setelah mengambil gelato
        me.payed_time = None # waktu setelah pembayaran
        me.gelato_time = None # waktu memasuki antrian pengambilan gelato
        me.target_position = None

    # fungsi untuk menggerakkan cust
    def move_towards_target(me, target_position=None): 
        if target_position is None:
            target_position = me.target_position
        
        if target_position is None:
            return

        x, y = me.position
        target_x, target_y = target_position
        if x < target_x:
            x = min(x + customer_speed, target_x)
        elif x > target_x:
            x = max(x - customer_speed, target_x)
        if y < target_y:
            y = min(y + customer_speed, target_y)
        elif y > target_y:
            y = max(y - customer_speed, target_y)
        me.position = (x, y)

class Cashier:
    def __init__(me, position):
        me.current_customer = None
        me.time_remaining = 0
        me.position = position
        me.queue = queue.Queue()
        me.customers_served = 0
        me.customers_paid = []

    def tick(me, current_time):
        if me.current_customer is not None:
            me.time_remaining -= 1
            if me.time_remaining <= 0:
                me.current_customer.getting_gelato = True
                me.current_customer.payed_time = current_time
                me.customers_paid.append(me.current_customer)
                me.current_customer = None
                me.customers_served += 1
        if me.current_customer is None and not me.queue.empty():
            me.start_next(me.queue.get(), current_time)

    def is_busy(me):
        return me.current_customer is not None

    def start_next(me, new_customer, current_time):
        me.current_customer = new_customer
        new_customer.service_start_time = current_time
        uniform_time = random.uniform(0.5, 1.0) * 60  # waktu pembayaran adalah random float
        me.time_remaining = uniform_time
        new_customer.target_position = (me.position[0], me.position[1] + cashier_size[1])

class Gelato:
    def __init__(me, position):
        me.current_customer = None
        me.position = position
        me.queue = queue.Queue()
        me.customers_served = 0
        me.time_remaining = 0

    def tick(me, current_time):
        if me.current_customer is not None:
            me.time_remaining -= 1
            if me.time_remaining <= 0:
                me.current_customer.exiting = True
                me.current_customer.departure_time = current_time
                me.current_customer = None
                me.customers_served += 1
        if me.current_customer is None and not me.queue.empty():
            me.start_next(me.queue.get(), current_time)

    def is_busy(me):
        return me.current_customer is not None

    def start_next(me, new_customer, current_time):
        me.current_customer = new_customer
        new_customer.service_start_time = current_time
        min_time = 1.5 * 60  
        max_time = 4.0 * 60  
        # waktu dipengaruhi oleh banyaknya item yang dibeli
        me.time_remaining = int(min_time + (max_time - min_time) * (new_customer.items / 5))
        new_customer.target_position = (me.position[0], me.position[1] + gelato_size[1])

def simulate(store_opening_time, total_customers, gelato_count, cashier_count):
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Simulasi Antrian Tempo Gelato")
    font = pygame.font.Font(None, 28)
    clock = pygame.time.Clock()

    # import image
    customer_img = pygame.transform.scale(pygame.image.load("tpscust.png"), customer_size)
    cashier_img = pygame.transform.scale(pygame.image.load("tpscashier.png"), cashier_size)
    gelato_img = pygame.transform.scale(pygame.image.load("tpsgelato.png"), gelato_size)

    # variabel: antrian, letak, waktu antrian
    custq = queue.Queue()
    cashiers = [Cashier((100 + 150 * i, 500)) for i in range(cashier_count)]
    gelatos = [Gelato((250 + 150 * i, 500)) for i in range(gelato_count)]
    arr_pay_times = []
    arr_gel_times = []
    all_customers = []
    completed_customers = [] 

    arrival_interval = 60  # interval antar kedatangan
    current_arrival_time = 0
    for _ in range(total_customers):
        arrival_time = random.randint(current_arrival_time, current_arrival_time + arrival_interval)
        current_arrival_time = arrival_time
        # pembelian : 2 - 5 scoops
        items = random.randint(2, 5)  
        customer = Customer(arrival_time, items)
        custq.put(customer)
        all_customers.append(customer)

    # simulasi dimulai
    current_time = 0
    running = True
    while running and (current_time < store_opening_time or not custq.empty() or any(gelato.is_busy() for gelato in gelatos)):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(WHITE)

        # memindahkan cust ke antrian pada kasir
        for customer in all_customers:
            if customer.arrival_time <= current_time:  
                if not customer.exiting:  
                    customer.move_towards_target()
                    screen.blit(customer_img, customer.position)

        # proses pada kasir
        while not custq.empty() and custq.queue[0].arrival_time <= current_time:
            customer = custq.get()
            available_cashier = min(cashiers, key=lambda c: c.queue.qsize())
            available_cashier.queue.put(customer)
            customer.target_position = (available_cashier.position[0], available_cashier.position[1] + customer_size[1])

        for cashier in cashiers:
            cashier.tick(current_time) # memperbarui variabel
            screen.blit(cashier_img, cashier.position) # menggambar kasir

            if cashier.current_customer:
                screen.blit(customer_img, cashier.current_customer.position) # menggambar cust

            for i, customer in enumerate(list(cashier.queue.queue)):
                target_pos = (cashier.position[0], cashier.position[1] - (i + 1) * customer_size[1]) # menggambar antrean
                customer.target_position = target_pos
                customer.move_towards_target()
                screen.blit(customer_img, customer.position)

        # memindahkan payed cust ke bagian gelato
        for cashier in cashiers:
            if cashier.customers_paid:
                for customer in cashier.customers_paid:
                    available_gelato = min(gelatos, key=lambda g: g.queue.qsize())
                    available_gelato.queue.put(customer)
                    customer.gelato_time = current_time
                    customer.target_position = (available_gelato.position[0], available_gelato.position[1] + customer_size[1])
                cashier.customers_paid.clear()

        for gelato in gelatos:
            gelato.tick(current_time) # pembaruan data
            screen.blit(gelato_img, gelato.position) # gambar pos gelato

            if gelato.current_customer:
                screen.blit(customer_img, gelato.current_customer.position)

            for i, customer in enumerate(list(gelato.queue.queue)):
                target_pos = (gelato.position[0], gelato.position[1] - (i + 1) * customer_size[1])
                customer.target_position = target_pos
                customer.move_towards_target()
                screen.blit(customer_img, customer.position)

        # memindahkan served cust ke exit position
        for gelato in gelatos:
            if gelato.current_customer and gelato.current_customer.exiting:
                gelato.current_customer.target_position = exit_position
                gelato.current_customer.move_towards_target(exit_position)
                screen.blit(customer_img, gelato.current_customer.position)
                if gelato.current_customer.position == exit_position:
                    completed_customers.append(gelato.current_customer)
                    gelato.current_customer = None

        # penghitungan statistik : rata-rata
        for customer in all_customers[:]:
            if customer.departure_time is not None:
                pay_waiting_time = customer.payed_time - customer.arrival_time
                gelato_waiting_time = customer.departure_time - customer.gelato_time
                arr_pay_times.append(pay_waiting_time)
                arr_gel_times.append(gelato_waiting_time)
                all_customers.remove(customer)

        served_customers = sum(gelato.customers_served for gelato in gelatos)
        if arr_pay_times:
            if cashier.current_customer:
                avg_pay_time = sum(arr_pay_times) / len(arr_pay_times) / 60  # Convert frames to seconds
        if arr_gel_times:
            avg_gel_time = sum(arr_gel_times) / len(arr_gel_times) / 60
        else:
            avg_pay_time = 0
            avg_gel_time = 0

        # display
        total_customers_text = font.render(f'Total customers: {total_customers}', True, BLACK)
        served_customers_text = font.render(f'Served customers: {served_customers}', True, BLACK)
        avg_pay_time_text = font.render(f'Avg waiting payment time: {avg_pay_time:.2f} sec', True, BLACK)
        avg_gel_time_text = font.render(f'Avg waiting gelato time: {avg_gel_time:.2f} sec', True, BLACK)
        total_customers_waiting_text = font.render(f'Waiting customers: {len(all_customers)}', True, BLACK)

        screen.blit(total_customers_text, (10, 10))
        screen.blit(served_customers_text, (10, 40))
        screen.blit(avg_pay_time_text, (10, 70))
        screen.blit(avg_gel_time_text, (10, 100))
        screen.blit(total_customers_waiting_text, (10, 130))

        pygame.display.flip()
        clock.tick(60)  
        current_time += 1

    pygame.quit()

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Tempo Gelato Queue Simulation - Main Menu")
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    menu_options = ["Hari Biasa", "Hari Libur"]
    config = {
        'Hari Biasa': {'total_customers': 100, 'staff_count': 3, 'cashier_count': 1},
        'Hari Libur': {'total_customers': 200, 'staff_count': 5, 'cashier_count': 1}
    }
    selected_option = 0

    while True:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    selected_day = menu_options[selected_option]
                    store_opening_time = 9000  
                    simulate(store_opening_time, config[selected_day]['total_customers'], config[selected_day]['staff_count'], config[selected_day]['cashier_count'])
                    return

        for i, option in enumerate(menu_options):
            color = BLACK
            if i == selected_option:
                color = (255, 0, 0)
            text = font.render(option, True, color)
            screen.blit(text, (screen_width // 2 - text.get_width() // 2, screen_height // 2 - text.get_height() // 2 + i * 40))

        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main_menu()