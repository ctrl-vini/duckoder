// Every text the student reads, in one place.

export const LOCALE = "pt-BR";

const listFormat = new Intl.ListFormat(LOCALE, { type: "conjunction" });

/** "o GPIO 13" or "os pinos D12 e D13", from the names of the pins a code uses. */
function pinList(names) {
  return names.length === 1 ? `o ${names[0]}` : `os pinos ${listFormat.format(names)}`;
}

export const UI_TEXT = {
  boardLabel: "placa:",
  boardPickerHint: "↑ e ↓ escolhem, enter confirma, esc fecha",
  clearConversation: "limpar conversa",
  showBoard: "ver placa",
  about: "sobre",
  close: "fechar",
  boardPaneLabel: "Placa e ligações",
  // Commands the page answers by itself, without the model. The first name is the main one.
  commands: {
    help: ["help", "ajuda"],
    pinout: ["pinout"],
    // Clear-screen commands students may know: Unix shells, Windows cmd and PowerShell, MATLAB.
    clear: ["clear", "cls", "reset", "clear-host", "clc"],
    about: ["about", "sobre"],
    quack: ["quack"],
  },
  help: {
    title: "comandos que o pato entende:",
    headers: ["comando", "o que faz", "atalho"],
    entries: [
      { command: "help", description: "mostra esta lista" },
      { command: "pinout", description: "mostra a placa e o que ligar para o código", key: "p" },
      { command: "clear", description: "limpa a conversa e começa do zero", key: "l" },
      { command: "about", description: "mostra o sobre do Duckoder", key: "s" },
      { command: "quack", description: "o pato faz quack" },
    ],
    aliases: (names) => ` (também: ${names.join(", ")})`,
    keys: "enter envia o pedido; shift + enter quebra a linha; ↑ e ↓ trazem de volta o que você já digitou nesta conversa",
  },
  clearDialogTitle: "Limpar a conversa?",
  clearDialogMessage:
    "As mensagens e o código saem da tela, e o pato esquece o que foi pedido até aqui.",
  clearDialogHint: "enter limpa, esc cancela",
  cancel: "cancelar",
  clear: "limpar",
  aboutDialog: {
    title: "Sobre o Duckoder",
    command: "duckoder --sobre",
    version: (version) => `versão ${version}`,
    description:
      "Plataforma web que gera código para placas didáticas a partir de pedidos em português, com um modelo de linguagem que roda na própria rede local.",
    details: [
      { label: "autor", value: "ctrl-vini", href: "https://github.com/ctrl-vini" },
      {
        label: "código",
        value: "github.com/ctrl-vini/duckoder",
        href: "https://github.com/ctrl-vini/duckoder",
      },
      {
        label: "licença",
        value: "GNU AGPL v3 ou posterior",
        href: "https://github.com/ctrl-vini/duckoder/blob/master/LICENSE",
      },
      { label: "fonte", value: "JetBrains Mono, sob a SIL Open Font License 1.1" },
    ],
    copyright: "© 2026 José Vinícius Alves de Oliveira. Software livre sob a GNU AGPL v3 ou posterior.",
  },
  wiringHeaders: ["componente", "pinos", "como ligar"],
  essentialPinsHeaders: ["pino", "para que serve"],
  essentialPinsHint:
    "em azul, os pinos que quase todo circuito usa; os componentes aparecem quando houver código",
  gpioName: (gpio) => `GPIO ${gpio}`,
  // A digital pin missing from the drawn header, such as the Mega's pins 22 to 53.
  digitalPinName: (gpio) => `D${gpio}`,
  pinWithRole: (name, role) => (role ? `${name} (${role})` : name),
  usageWithRole: (name, role) => (role ? `${name} (${role})` : name),
  noPinout: "esta placa não tem a pinagem cadastrada; veja só a tabela de ligações",
  ideBoard: (name) => `na Arduino IDE, selecione a placa ${name}`,
  showWiring: "ver ligações",
  fullBoard: "placa completa",
  versionWiring: (version) => `ligações da versão ${version}`,
  wiringOfVersion: (version) => `ligações da versão ${version}: só o que o código usa`,
  noComponentsUsed: (version) => `o código da versão ${version} não usa nenhum componente da placa`,
  unlistedGpios: (names) =>
    `atenção: o código usa ${pinList(names)}, mas não há componente ligado ${names.length === 1 ? "nele" : "neles"}`,
  unlistedPinNote: "sem componente",
  movedPin: (component, fromName, toName, pinLabel) =>
    `${component} mudou do ${fromName} para o ${toName}: ligue o fio no ${pinLabel}`,
  componentDrawing: {
    labels: {
      led: "LED",
      button: "BOTÃO",
      buzzer: "BUZZER",
      dht22: "DHT22",
      potentiometer: "POT",
      oled: "OLED",
      relay: "RELÉ",
    },
    legs: {
      anode: "+ perna longa",
      cathode: "− perna curta",
      terminal: "terminal",
      positive: "+ positivo",
      negative: "− negativo",
      vcc: "VCC",
      gnd: "GND",
      data: "DATA",
      end: "ponta",
      wiper: "meio",
      scl: "SCL",
      sda: "SDA",
      in: "IN",
    },
    parts: { resistor: "resistor" },
    unknownPin: "?",
  },
  requestLabel: "O que a placa deve fazer?",
  send: "enviar",
  sendHint: "enter envia, shift + enter quebra a linha, ↑ ↓ histórico",
  promptUser: "aluno@lab",
  promptPath: "~",
  duckSpeaker: "pato>",
  errorLabel: "erro:",
  commentPrefix: "#",
  pendingReply: {
    // Shown in order while the model writes, one every few seconds.
    steps: [
      "lendo o seu pedido",
      "consultando o perfil da placa",
      "escolhendo os pinos",
      "escrevendo o setup()",
      "escrevendo o loop()",
      "conferindo as ligações",
      "revisando o código",
      "preparando a explicação",
    ],
    // Then, for long generations, one of these at random.
    stillWaiting: [
      "ainda pensando no código",
      "o modelo está caprichando",
      "quase lá",
      "só mais um pouquinho",
      "contando os pinos de novo",
    ],
  },
  copy: "copiar",
  copied: "copiado",
  copyFailed: "selecione e copie",
  codeVersion: (version) => `versão ${version}`,
  generatedBy: (model, duration) => `gerado por ${model} em ${duration}`,
  noCode: "esta resposta veio sem código",
  sameCodeAs: (version) => `o código é igual ao da versão ${version}`,
  motd: {
    title: "Duckoder",
    lines: [
      "Gera código para placas didáticas com um modelo de linguagem da rede local.",
      "Explique ao pato o que a placa deve fazer, como explicaria a um colega. O código volta pronto para colar na IDE, e você pode pedir ajustes na mesma conversa.",
      "Digite help para ver os comandos e os atalhos.",
    ],
    examplesTitle: "Experimente um destes:",
    examples: [
      "Pisque o LED embutido a cada segundo",
      "Acenda o LED vermelho enquanto o botão estiver pressionado",
      "Mostre a temperatura do DHT22 no monitor serial",
    ],
  },
  duck: {
    listening: "Quack! Me explica o que a placa deve fazer.",
    thinking: [
      "Hmm, deixa eu pensar",
      "Quack... pensando",
      "Deixa eu olhar os pinos",
      "Um momento, estou montando o código",
      "Boa! Já estou escrevendo",
      "Pensando com todas as penas",
    ],
    happy: (version) => `Pronto! A versão ${version} está no terminal.`,
    noCode: "Não saiu código desta vez. Tenta explicar de outro jeito?",
    unchanged: (version) =>
      `Hmm, o código saiu igual à versão ${version}. Tenta pedir de outro jeito?`,
    confused: "Quack?! Algo deu errado. Olha a mensagem de erro.",
    board: "Abri a placa num painel. Quando houver código, eu mostro o que ligar em cada pino.",
    wiring: (version) =>
      `Essas são as ligações da versão ${version}. Os pinos em amarelo são os que o código usa.`,
    noComponents: (version) => `A versão ${version} não usa nenhum componente da placa.`,
    movedPins: (version, count) =>
      count === 1
        ? `Na versão ${version}, um componente mudou de pino. Muda o fio de lugar também!`
        : `Na versão ${version}, alguns componentes mudaram de pino. Muda os fios de lugar também!`,
    unlistedGpios: (version, names) =>
      `Hmm, a versão ${version} usa ${pinList(names)}, e não tem nada ligado ${names.length === 1 ? "nele" : "neles"}.`,
    help: "Esses são os comandos que eu entendo.",
    quacks: ["Quack!", "Quack quack!", "QUACK!"],
  },
  conversationNotFound: "a conversa do link não existe mais; comece uma nova conversa",
  noBoards: "nenhuma placa cadastrada no servidor; adicione um perfil em data/boards e reinicie",
  errors: {
    0: "não foi possível falar com o servidor; confira se ele está rodando e se você está na mesma rede",
    404: "conversa ou placa não encontrada; comece uma nova conversa",
    422: "escreva o pedido antes de enviar, com até 4.000 caracteres",
    429: "o servidor já respondeu o máximo de pedidos desta hora; tente de novo mais tarde",
    502: "o modelo de linguagem não respondeu; confira se o serviço do modelo está no ar e envie de novo",
  },
  unexpectedError: "o servidor não conseguiu atender o pedido; envie de novo",
};

/** Message to show for a failed API call, based on its HTTP status. */
export function errorMessageFor(error) {
  return UI_TEXT.errors[error.status] ?? UI_TEXT.unexpectedError;
}
