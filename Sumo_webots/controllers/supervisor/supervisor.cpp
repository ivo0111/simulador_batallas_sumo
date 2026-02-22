#include <webots/Supervisor.hpp>
#include <iostream>
#include <string>
#include <sstream>
#include <cstdlib>
#include <winsock2.h>
#include <ws2tcpip.h>

using namespace webots;

enum class MatchStatus
{
    WAITING,
    ROUND_ACTIVE,
    ROUND_END,
    MATCH_END // al mejor de 3, o cuantas rondas de indiquen
};

enum class Winner
{
    NONE,
    ROBOT_A,
    ROBOT_B
};

struct MatchState
{
    int roundNumber = 0;
    int scoreA = 0;
    int scoreB = 0;
    MatchStatus status = MatchStatus::WAITING;
    Winner lastRoundWinner = Winner::NONE;
    Winner matchWinner = Winner::NONE;
    double roundStartTime = 0.0;
    double roundElapsedTime = 0.0;
};

class TournamentSupervisor
{
public:
    TournamentSupervisor(Supervisor *sup, int port_arg = 54000)
        : supervisor(sup), port(port_arg)
    {
        initSocket();

        robotA = supervisor->getFromDef("robot_A");
        robotB = supervisor->getFromDef("robot_B");
        port = port_arg;

        roundsToWin = 2; // mejor de 3
        roundTimeLimit = 60.0;
        ringHeight = 0.03; // altura a la que está el ring para detectar ring out
    }

    void startMatch()
    {
        state = MatchState();
        state.status = MatchStatus::ROUND_ACTIVE;
        state.roundNumber = 1;
        state.roundStartTime = supervisor->getTime();
        std::cout << "MATCH START\n";
        emitState();
    }

    void update()
    {
        acceptClient();
        if (state.status != MatchStatus::ROUND_ACTIVE)
            return;
        state.roundElapsedTime = supervisor->getTime() - state.roundStartTime;

        emitState();

        // timeout
        if (state.roundElapsedTime >= roundTimeLimit)
        {
            endRound(Winner::NONE);
            return;
        }

        // ring out
        if (isOut(robotA))
            endRound(Winner::ROBOT_B);
        else if (isOut(robotB))
            endRound(Winner::ROBOT_A);
    }

    bool isMatchOver() const
    {
        return state.status == MatchStatus::MATCH_END;
    }

private:
    Supervisor *supervisor;
    Node *robotA;
    Node *robotB;
    MatchState state;
    WSADATA wsaData;
    SOCKET serverSocket = INVALID_SOCKET;
    SOCKET clientSocket = INVALID_SOCKET;

    bool clientConnected = false;
    int roundsToWin;
    double roundTimeLimit;
    double ringHeight;

    bool isOut(Node *robot)
    {
        const double *pos = robot->getPosition();
        return pos[2] < ringHeight;
    }

    void endRound(Winner winner)
    {
        state.lastRoundWinner = winner;

        if (winner == Winner::ROBOT_A)
            state.scoreA++;
        else if (winner == Winner::ROBOT_B)
            state.scoreB++;

        if (state.scoreA >= roundsToWin || state.scoreB >= roundsToWin)
        {
            state.status = MatchStatus::MATCH_END;
            state.matchWinner = (state.scoreA > state.scoreB)
                                    ? Winner::ROBOT_A
                                    : Winner::ROBOT_B;
            emitState();
            if (clientConnected)
            {
                closesocket(clientSocket);
            }
            closesocket(serverSocket);
            WSACleanup();
            supervisor->simulationQuit(0); // termina la simulación
            return;
        }

        // siguiente round
        state.roundNumber++;
        resetWorld();
        emitState();
        state.roundStartTime = 0.0;
    }

    void resetWorld()
    {
        supervisor->simulationResetPhysics(); // pausa el movimiento
        robotA->restartController();
        robotB->restartController();
        supervisor->simulationReset(); // reinicia la simulación
    }

    void initSocket()
    {
        WSAStartup(MAKEWORD(2, 2), &wsaData);

        serverSocket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

        sockaddr_in service;
        service.sin_family = AF_INET;
        service.sin_addr.s_addr = inet_addr("127.0.0.1");
        service.sin_port = htons(port);

        bind(serverSocket, (SOCKADDR *)&service, sizeof(service));

        listen(serverSocket, 1);

        // modo no bloqueante
        u_long mode = 1;
        ioctlsocket(serverSocket, FIONBIO, &mode); // FIONBIO para no bloqueante

        std::cout << "TCP server listening on 127.0.0.1:" << port << std::endl;
    }

    void acceptClient()
    {
        if (clientConnected)
            return;

        clientSocket = accept(serverSocket, NULL, NULL);
        if (clientSocket != INVALID_SOCKET)
        {
            clientConnected = true;
            std::cout << "Client connected" << std::endl;
        }
    }

    void sendMessage(const std::string &msg) const
    {
        if (!clientConnected)
            return;

        std::string data = msg + "\n";
        send(clientSocket, data.c_str(), (int)data.size(), 0);
    }

    void emitState() const
    {
        std::ostringstream oss;
        oss << "{"
            << "\"round\":" << state.roundNumber << ","
            << "\"scoreA\":" << state.scoreA << ","
            << "\"scoreB\":" << state.scoreB << ","
            << "\"status\":\"" << statusToString(state.status) << "\"," \
            << "\"lastRoundWinner\":\"" << winnerToString(state.lastRoundWinner) << "\"," \
            << "\"matchWinner\":\"" << winnerToString(state.matchWinner) << "\"," \
            << "\"elapsed\":" << state.roundElapsedTime
            << "}";

        std::string json = oss.str();
        sendMessage(json);
    }

    std::string statusToString(MatchStatus s) const
    {
        switch (s)
        {
        case MatchStatus::WAITING:
            return "WAITING";
        case MatchStatus::ROUND_ACTIVE:
            return "ROUND_ACTIVE";
        case MatchStatus::ROUND_END:
            return "ROUND_END";
        case MatchStatus::MATCH_END:
            return "MATCH_END";
        }
        return "UNKNOWN";
    }

    std::string winnerToString(Winner w) const
    {
        switch (w)
        {
        case Winner::NONE:
            return "NONE";
        case Winner::ROBOT_A:
            return "ROBOT_A";
        case Winner::ROBOT_B:
            return "ROBOT_B";
        }
        return "NONE";
    }
};

int main(int argc, char **argv)
{
    Supervisor supervisor;
    int timeStep = supervisor.getBasicTimeStep();

    int port = 54000;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg.rfind("--port=", 0) == 0) {
            try {
                port = std::stoi(arg.substr(7));
            } catch (...) {
                std::cerr << "Invalid port value\n";
                return 1;
            }
        }
    }

    TournamentSupervisor tournament(&supervisor, port);
    tournament.startMatch();

    while (supervisor.step(timeStep) != -1)
    {
        tournament.update();
        if (tournament.isMatchOver())
            break;
    }

    return 0;
}