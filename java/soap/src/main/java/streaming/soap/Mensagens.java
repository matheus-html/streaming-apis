package streaming.soap;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import javax.xml.stream.XMLOutputFactory;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.XMLStreamWriter;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import streaming.core.Conflito;
import streaming.core.Invalido;
import streaming.core.NaoEncontrado;
import streaming.core.Pagina;
import streaming.core.Recurso;
import streaming.core.Servicos;
import streaming.soap.Contrato.Elemento;
import streaming.soap.Contrato.Operacao;

public final class Mensagens {

    public static final String ENV = "http://schemas.xmlsoap.org/soap/envelope/";
    private static final String NS = Contrato.NS;

    public record Resposta(int status, byte[] corpo) {
    }

    @FunctionalInterface
    interface Manipulador {
        Object executar(Map<String, Object> argumentos);
    }

    private static final DocumentBuilderFactory FABRICA = criarFabrica();
    private static final ThreadLocal<DocumentBuilder> CONSTRUTOR = ThreadLocal.withInitial(Mensagens::novoConstrutor);
    private static final ThreadLocal<XMLOutputFactory> SAIDA = ThreadLocal.withInitial(XMLOutputFactory::newFactory);
    private static final Map<String, Manipulador> TRATADORES = tratadores();

    private Mensagens() {
    }

    private static DocumentBuilderFactory criarFabrica() {
        try {
            DocumentBuilderFactory fabrica = DocumentBuilderFactory.newInstance();
            fabrica.setNamespaceAware(true);
            fabrica.setXIncludeAware(false);
            fabrica.setExpandEntityReferences(false);
            fabrica.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            fabrica.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            return fabrica;
        } catch (ParserConfigurationException erro) {
            throw new IllegalStateException(erro);
        }
    }

    private static DocumentBuilder novoConstrutor() {
        try {
            DocumentBuilder construtor = FABRICA.newDocumentBuilder();
            construtor.setErrorHandler(new ErrorHandler() {
                @Override
                public void warning(SAXParseException erro) {
                }

                @Override
                public void error(SAXParseException erro) {
                }

                @Override
                public void fatalError(SAXParseException erro) throws SAXException {
                    throw erro;
                }
            });
            return construtor;
        } catch (ParserConfigurationException erro) {
            throw new IllegalStateException(erro);
        }
    }

    private static Map<String, Manipulador> tratadores() {
        Map<String, Manipulador> mapa = new HashMap<>();
        for (Contrato.Recurso recurso : Contrato.RECURSOS) {
            Recurso servico = switch (recurso.tipo()) {
                case "Usuario" -> Servicos.USUARIOS;
                case "Musica" -> Servicos.MUSICAS;
                default -> Servicos.PLAYLISTS;
            };
            String nome = recurso.nome();
            mapa.put("Listar" + recurso.plural(), a -> servico.listar(
                    (Integer) a.get("pagina"), (Integer) a.get("tamanho"), (String) a.get("nome")));
            mapa.put("Obter" + recurso.tipo(), a -> servico.obter((Integer) a.get("id")));
            mapa.put("Criar" + recurso.tipo(), a -> servico.criar(objeto(a.get(nome))));
            mapa.put("Atualizar" + recurso.tipo(), a -> servico.atualizar((Integer) a.get("id"),
                    objeto(a.get(nome))));
            mapa.put("Remover" + recurso.tipo(), a -> {
                servico.remover((Integer) a.get("id"));
                return null;
            });
        }
        mapa.put("ListarPlaylistsDoUsuario", a -> Servicos.playlistsDoUsuario(
                (Integer) a.get("id"), (Integer) a.get("pagina"), (Integer) a.get("tamanho")));
        mapa.put("ListarMusicasDaPlaylist", a -> Servicos.musicasDaPlaylist(
                (Integer) a.get("id"), (Integer) a.get("pagina"), (Integer) a.get("tamanho")));
        mapa.put("ListarPlaylistsDaMusica", a -> Servicos.playlistsDaMusica(
                (Integer) a.get("id"), (Integer) a.get("pagina"), (Integer) a.get("tamanho")));
        return mapa;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> objeto(Object valor) {
        return (Map<String, Object>) valor;
    }

    private static List<Element> filhos(Element pai) {
        List<Element> lista = new ArrayList<>();
        for (Node no = pai.getFirstChild(); no != null; no = no.getNextSibling()) {
            if (no.getNodeType() == Node.ELEMENT_NODE) {
                lista.add((Element) no);
            }
        }
        return lista;
    }

    private static Element filho(Element pai, String nome) {
        for (Node no = pai.getFirstChild(); no != null; no = no.getNextSibling()) {
            if (no.getNodeType() == Node.ELEMENT_NODE && nome.equals(no.getLocalName())) {
                return (Element) no;
            }
        }
        return null;
    }

    private static String baseDoTipo(String tipo) {
        return tipo.endsWith("?") ? tipo.substring(0, tipo.length() - 1) : tipo;
    }

    private static int inteiro(String texto, String nome) {
        try {
            return Integer.parseInt(texto.trim());
        } catch (NumberFormatException erro) {
            throw new Invalido("campo '" + nome + "' deve ser um inteiro");
        }
    }

    static Object ler(Element elemento, String tipo, String nome) {
        String base = baseDoTipo(tipo);
        String texto = elemento.getTextContent();
        switch (base) {
            case "texto":
                return texto;
            case "inteiro":
                return inteiro(texto, nome);
            case "longo":
                try {
                    return Long.parseLong(texto.trim());
                } catch (NumberFormatException erro) {
                    throw new Invalido("campo '" + nome + "' deve ser um inteiro");
                }
            case "booleano": {
                String valor = texto.trim().toLowerCase();
                if (!valor.equals("true") && !valor.equals("false") && !valor.equals("1") && !valor.equals("0")) {
                    throw new Invalido("campo '" + nome + "' deve ser booleano");
                }
                return valor.equals("true") || valor.equals("1");
            }
            case "decimal":
                try {
                    return Double.parseDouble(texto.trim());
                } catch (NumberFormatException erro) {
                    throw new Invalido("campo '" + nome + "' deve ser numérico");
                }
            case "lista_texto": {
                List<Object> itens = new ArrayList<>();
                for (Element item : filhos(elemento)) {
                    itens.add(item.getTextContent());
                }
                return itens;
            }
            case "lista_int": {
                List<Object> itens = new ArrayList<>();
                for (Element item : filhos(elemento)) {
                    itens.add(inteiro(item.getTextContent(), nome));
                }
                return itens;
            }
            default:
                break;
        }
        if (base.startsWith("obj:")) {
            return lerObjeto(elemento, base.substring(4));
        }
        if (base.startsWith("lista:")) {
            List<Object> itens = new ArrayList<>();
            for (Element item : filhos(elemento)) {
                itens.add(lerObjeto(item, base.substring(6)));
            }
            return itens;
        }
        throw new Invalido("tipo desconhecido para '" + nome + "'");
    }

    static Map<String, Object> lerObjeto(Element elemento, String tipo) {
        Map<String, Object> dados = new LinkedHashMap<>();
        for (Elemento campo : Contrato.TIPOS.get(tipo)) {
            Element no = filho(elemento, campo.nome());
            if (no != null) {
                dados.put(campo.nome(), ler(no, campo.tipo(), campo.nome()));
            }
        }
        return dados;
    }

    static Map<String, Object> argumentos(Element requisicao, String operacao) {
        Operacao definicao = Contrato.OPERACOES.get(operacao);
        Map<String, Object> valores = new HashMap<>();
        for (Elemento campo : definicao.requisicao()) {
            Element no = filho(requisicao, campo.nome());
            if (no == null) {
                if (!campo.tipo().endsWith("?")) {
                    throw new Invalido("campo '" + campo.nome() + "' é obrigatório");
                }
                valores.put(campo.nome(), null);
            } else {
                valores.put(campo.nome(), ler(no, campo.tipo(), campo.nome()));
            }
        }
        return valores;
    }

    private static String texto(Object valor) {
        return String.valueOf(valor);
    }

    private static void texto(XMLStreamWriter saida, String nome, String conteudo) throws XMLStreamException {
        saida.writeStartElement("tns", nome, NS);
        saida.writeCharacters(conteudo);
        saida.writeEndElement();
    }

    static void escrever(XMLStreamWriter saida, String nome, Object valor, String tipo) throws XMLStreamException {
        if (valor == null) {
            return;
        }
        String base = baseDoTipo(tipo);
        saida.writeStartElement("tns", nome, NS);
        if (base.equals("lista_texto") || base.equals("lista_int")) {
            for (Object item : (List<?>) valor) {
                texto(saida, "item", texto(item));
            }
        } else if (base.startsWith("obj:")) {
            escreverCampos(saida, (Map<?, ?>) valor, base.substring(4));
        } else if (base.startsWith("lista:")) {
            for (Object item : (List<?>) valor) {
                saida.writeStartElement("tns", "item", NS);
                escreverCampos(saida, (Map<?, ?>) item, base.substring(6));
                saida.writeEndElement();
            }
        } else {
            saida.writeCharacters(texto(valor));
        }
        saida.writeEndElement();
    }

    static void escreverCampos(XMLStreamWriter saida, Map<?, ?> dados, String tipo) throws XMLStreamException {
        for (Elemento campo : Contrato.TIPOS.get(tipo)) {
            if (dados.containsKey(campo.nome())) {
                escrever(saida, campo.nome(), dados.get(campo.nome()), campo.tipo());
            }
        }
    }

    private static XMLStreamWriter abrir(ByteArrayOutputStream destino) throws XMLStreamException {
        XMLStreamWriter saida = SAIDA.get().createXMLStreamWriter(destino, "UTF-8");
        saida.writeStartDocument("UTF-8", "1.0");
        saida.writeStartElement("soap", "Envelope", ENV);
        saida.writeNamespace("soap", ENV);
        saida.writeNamespace("tns", NS);
        saida.writeStartElement("soap", "Body", ENV);
        return saida;
    }

    private static byte[] fechar(XMLStreamWriter saida, ByteArrayOutputStream destino) throws XMLStreamException {
        saida.writeEndElement();
        saida.writeEndElement();
        saida.writeEndDocument();
        saida.close();
        return destino.toByteArray();
    }

    static byte[] montarResposta(String operacao, Object resultado) {
        try {
            ByteArrayOutputStream destino = new ByteArrayOutputStream(4096);
            XMLStreamWriter saida = abrir(destino);
            saida.writeStartElement("tns", operacao + "Response", NS);
            String[] resposta = Contrato.OPERACOES.get(operacao).resposta();
            if (resposta[0].equals("entidade")) {
                escrever(saida, resposta[1], resultado, "obj:" + resposta[2]);
            } else if (resposta[0].equals("pagina")) {
                Pagina pagina = (Pagina) resultado;
                for (Map<String, Object> item : pagina.itens()) {
                    escrever(saida, resposta[1], item, "obj:" + resposta[2]);
                }
                escrever(saida, "pagina", pagina.pagina(), "inteiro");
                escrever(saida, "tamanho", pagina.tamanho(), "inteiro");
                escrever(saida, "total", pagina.total(), "longo");
            }
            saida.writeEndElement();
            return fechar(saida, destino);
        } catch (XMLStreamException erro) {
            throw new IllegalStateException(erro);
        }
    }

    static byte[] falha(String codigo, String mensagem) {
        try {
            ByteArrayOutputStream destino = new ByteArrayOutputStream(512);
            XMLStreamWriter saida = abrir(destino);
            saida.writeStartElement("soap", "Fault", ENV);
            saida.writeStartElement("faultcode");
            saida.writeCharacters("soap:Client");
            saida.writeEndElement();
            saida.writeStartElement("faultstring");
            saida.writeCharacters(mensagem);
            saida.writeEndElement();
            saida.writeStartElement("detail");
            texto(saida, "codigo", codigo);
            saida.writeEndElement();
            saida.writeEndElement();
            return fechar(saida, destino);
        } catch (XMLStreamException erro) {
            throw new IllegalStateException(erro);
        }
    }

    private static Element analisar(byte[] corpo) {
        try {
            DocumentBuilder construtor = CONSTRUTOR.get();
            construtor.reset();
            Document documento = construtor.parse(new ByteArrayInputStream(corpo));
            return documento.getDocumentElement();
        } catch (SAXException erro) {
            throw new Invalido("XML malformado");
        } catch (IOException erro) {
            throw new IllegalStateException(erro);
        }
    }

    public static Resposta processar(byte[] corpo) {
        try {
            Element raiz = analisar(corpo);
            if (!"Envelope".equals(raiz.getLocalName())) {
                throw new Invalido("o elemento raiz deve ser Envelope");
            }
            Element conteudo = filho(raiz, "Body");
            List<Element> itens = conteudo == null ? List.of() : filhos(conteudo);
            if (itens.isEmpty()) {
                throw new Invalido("Body vazio");
            }
            Element requisicao = itens.get(0);
            String operacao = requisicao.getLocalName();
            Manipulador manipulador = TRATADORES.get(operacao);
            if (manipulador == null) {
                throw new Invalido("operação desconhecida: " + operacao);
            }
            Object resultado = manipulador.executar(argumentos(requisicao, operacao));
            return new Resposta(200, montarResposta(operacao, resultado));
        } catch (NaoEncontrado erro) {
            return new Resposta(500, falha("NAO_ENCONTRADO", erro.getMessage()));
        } catch (Invalido erro) {
            return new Resposta(500, falha("ENTRADA_INVALIDA", erro.getMessage()));
        } catch (Conflito erro) {
            return new Resposta(500, falha("CONFLITO", erro.getMessage()));
        }
    }
}