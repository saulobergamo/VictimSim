from datetime import datetime
import math
import random
from pprint import pprint

class Genetic:
    def __init__(self, populationSize, victims, walls, totalTime):
        self.totalTime = totalTime
        self.mutation_rate = 0.5
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, 1), (1, -1)]
        self.populationSize = populationSize
        self.walls = walls
        self.totalVictims = len(victims)

        self.victimPos = self.setVictims(victims)
        self.victimDistances = {}

        self.population = self.genesis()
        self.setDistances()


    def genesis(self):
        # Selecionando todas as vítimas, exceto a primeira
        victims = list(self.victimPos.keys())[1:]

        # Inicializando a população
        population = []

        # Criando cada cromossomo da população
        for i in range(self.populationSize):
            # Embaralhando as vítimas aleatoriamente
            random.shuffle(victims)

            # Adicionando a primeira e última posição do cromossomo
            chromossome = [0] + victims + [0]

            # Adicionando o cromossomo na população
            population.append(chromossome)

        # Retornando a população inicial
        return population


    def setDistances(self):
        # not_computed_victims = list(self.victimPos.keys())
        for victim in self.victimPos.keys():
            self.victimDistances[victim] = {}
            self.distancesCalc(victim)

    
    def distancesCalc(self, victim):
        # contador para controlar o número de vítimas encontradas
        victimsCounter = 0        
        # nó inicial para busca em largura (coordenada da vítima e trajetória até ela)
        initialPos = (self.victimPos[victim]["coord"], [])

        # lista de nós vizinhos de busca
        neighbors = [initialPos]

        # lista de nós explorados
        visited = []

        # realiza a busca em largura até encontrar todas as vítimas
        while True:
            # se não há mais nós vizinhos, termina a busca
            if len(neighbors) == 0:
                return

            # seleciona o próximo nó vizinho
            node = neighbors.pop(0)

            # adiciona o nó na lista de nós explorados
            visited.append(node[0])

            # para cada possível movimento a partir do nó atual
            for move in self.directions:
                # cria um novo nó filho com a nova coordenada e trajetória atualizada
                child = ((node[0][0] + move[0], node[0][1] + move[1]), node[1] + [move])

                # se a coordenada do novo nó não está bloqueada, nem foi explorada ou adicionada à fronteira
                if child[0] not in self.walls + visited + [n[0] for n in neighbors]:
                    # verifica se a nova coordenada corresponde a uma vítima
                    for victimPos, victim_info in self.victimPos.items():
                        if child[0] == victim_info["coord"]:
                            # calcula a trajetória e custo do nó filho até a vítima e adiciona no dicionário de distâncias
                            self.victimDistances[victim][victimPos] = {"trajectory": child[1], "cost": self.costCalc(child[1])}
                            victimsCounter += 1

                            # se já encontrou todas as vítimas, termina a busca
                            if victimsCounter == self.totalVictims:
                                return

                    # adiciona o nó filho vizinho
                    neighbors.append(child)


    def costCalc(self, trajectory):
        cost = 0
        for move in trajectory:
            # Se o movimento for diagonal, adiciona 1.5 no custo total, senão adiciona 1
            if move[0] != 0 and move[1] != 0:
                cost += 1.5
            else:
                cost += 1
        return cost

    def setVictims(self, victims):
        victimDict = {}
        i = 1
        # Define a primeira vítima como origem (coordenadas (0, 0) e gravidade 0)
        victimDict[0] = {"coord": (0, 0), "severity": 0}
        # Adiciona cada vítima à lista de vítimas, com um índice único e suas informações de gravidade e coordenadas
        for victim in victims:
            victimDict[i] = {"coord": victim[0], "severity": victim[1]}
            i += 1
        return victimDict

    def fitnessCalc(self, victims):
        totalTime = 0
        points = 0
        # Calcula a distância percorrida entre cada par de vítimas consecutivas
        for i in range(self.totalVictims-1):
            a = victims[i]
            b = victims[i + 1]
            totalTime += self.victimDistances[a][b]["cost"]
        # Se o tempo total exceder o tempo máximo permitido, remove a última vítima e recalcula o fitness
        if totalTime >= self.totalTime:
            del victims[-2]
            return self.fitnessCalc(victims)
        # Calcula a pontuação com base na gravidade de cada vítima
        for victim in victims:
            if self.victimPos[victim]["severity"] == '1':
                points += 8
            if self.victimPos[victim]["severity"] == '2':
                points += 4
            if self.victimPos[victim]["severity"] == '3':
                points += 2
            if self.victimPos[victim]["severity"] == '4':
                points += 1

        fit = points / totalTime * 100

        return fit

    def getFitness(self):
        # cria uma lista de zeros com comprimento igual ao tamanho da população
        fitnes_list = [0] * self.populationSize
        # itera através da população e avalia o fitness de cada indivíduo
        for i in range(self.populationSize):
            fitnes_list[i] = self.fitnessCalc(self.population[i])
        
        return fitnes_list


    def setParent(self):
        # soma de todos os valores de fitness na lista de fitness
        fitSum = sum(self.fitList)
        # cria uma lista de probabilidades de seleção de progenitor com base nos valores de fitness normalizados
        prob = [fit / fitSum for fit in self.fitList]
        # seleciona aleatoriamente os pais de cada indivíduo na população
        parentA = [random.choices(self.population, weights=prob, k=1)[0] for _ in range(len(self.population))]
        parentB = [random.choices(self.population, weights=prob, k=1)[0] for _ in range(len(self.population))]

        return [parentA, parentB]


    def procreation(self, parentA, parentB):
        # cria uma lista de filhos inicialmente contendo os primeiros 'n' elementos
        # do progenitor A, onde 'n' é igual à metade do número total de vítimas
        children = parentA[0:math.floor(self.totalVictims/2)]
        # adiciona vítimas do progenitor B à lista de filhos,
        #  desde que a vítima ainda não esteja presente
        for parent in parentB:
            if parent not in children:
                children.append(parent)

        return children + [0]


    def crossOver(self, parentList):
        population = []
        for i in range(len(parentList[0])):
            children = self.procreation(parentList[0][i], parentList[1][i])
            population.append(children)
        return population


    def mutation(self, children):
        # Itera e troca a posição de dois genes/vítimas aleatórias
        for i in range(int(self.totalVictims * self.mutation_rate)):
            a = random.randint(1, self.totalVictims-1)
            b = random.randint(1, self.totalVictims-1)
            aux = children[a]
            children[a] = children[b]
            children[b] = aux            
        return children


    def populationMutation(self, population):
        mutated = []
        for children in population:
            mutated_children = self.mutation(children)
            mutated.append(mutated_children)
        return mutated

    def _run(self):
        self.fitList = self.getFitness()
        response = [-1, 0, []]
        fitMax = max(self.fitList)
        fitAvg = sum(self.fitList) / len(self.fitList)
        for i in range(self.totalVictims * 100):
            if i % 100 == 0:
                print(i, fitMax, fitAvg)

            # Saving the best solution            
        if fitMax > response[1]:
            response[0] = i
            response[1] = fitMax
            response[2] = [self.population[i] for i in range(len(self.population)) if self.fitList[i] == fitMax]

        parentList = self.setParent()
        population = self.crossOver(parentList)
        self.population = self.populationMutation(population)

        return response, self.victimDistances

