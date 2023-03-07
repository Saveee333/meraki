from random import randint

class Player:
    hp = 100
    damage = 10

# Записываем в переменную, чтобы было удобно.
p = Player()

class Enemy:
    # Рандомно получает хп врага от 70 до 130, рандомно получает дамаг врага от 6 до 13.
    hp = randint(70,130)
    damage = randint(6,13)

# Записываем в переменную, чтобы было удобно.
e = Enemy()

def menu(p):
    while True:
        print("1) Сражаться")
        print("2) Посмотреть статистику")
        # try и except просто фиксят ошибки. Не обращайте внимания.
        try:
            n = input("Введите число: ")

            if n == 1:
                menu_fight(p)
            if n == 2:
                menu_stats(p)
            else:
                print("Чего ждем?")

        except NameError:
            print("Введите число")
        except SyntaxError:
            print("Введите число")

def menu_stats(p):
    print("Статистика игрока")
    print("*****************")
    # Попробую обьяснить, что значит %s. Она по последовательности списка вписывает в %s переменную.
    print("hp %s."%(p.hp))
    print(f"Вы hp: {p.hp} damage: {p.damage}")
    print("damage %s."%(p.damage))
    input("Нажмите Enter для продолжения.")

def menu_fight(p):
    while e.hp > 0:
        # Также, как я и сказал по последовательности списка расставляет переменные.
        print("Вы hp: %s damage: %s")%(p.hp, p.damage)
        print("Враг hp: %s damage: %s")%(e.hp, e.damage)
        print("**********************")
        print("1)Ударить")
        print("2)Хил 0-5")
        n = input("Введите число: ")
        if n == 1:
            # Здоровье врага отнимает от вашего дамага.
            e.hp -= p.damage
            print("Вы ударили противника, у него осталось %s hp")%(e.hp)
            # Здоровье игрока отнимает от дамага врага.
            p.hp -= e.damage
            print("Противник ударил вас, у вас осталось %s hp")%(p.hp)

            print("*********************")

        if n == 2:
            # Рандомно от 0 до 5 добавляет хп.
            p.hp += randint(0,5)
            # Если здоровье игрока больше, то хп игрока будет равна 100.
            if p.hp > 100:
                p.hp = 100

            print("Ваши хп %s")%(p.hp)

        else:
             print("Чего ждем?")
        if p.hp < 0:
            print("Вы проиграли")
        if e.hp < 0:
            print("Вы победили")

        print("******************")

# Вызов меню.
menu(p)