package streaming.grpc;

import com.google.protobuf.Descriptors.FieldDescriptor;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.Message;
import com.google.protobuf.util.JsonFormat;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import streaming.Streaming.ListarRelacionadosRequisicao;
import streaming.Streaming.ListarRequisicao;
import streaming.core.Conflito;
import streaming.core.Invalido;
import streaming.core.Json;
import streaming.core.NaoEncontrado;
import streaming.core.Pagina;
import streaming.core.Recurso;

final class Ponte {

    interface Relacionados {
        Pagina buscar(int id, Integer pagina, Integer tamanho);
    }

    private static final JsonFormat.Printer IMPRESSORA = JsonFormat.printer();
    private static final JsonFormat.Parser LEITOR = JsonFormat.parser().ignoringUnknownFields();

    private Ponte() {
    }

    static Map<String, Object> dados(Message entrada) {
        Map<String, Object> resultado = new LinkedHashMap<>();
        for (Map.Entry<FieldDescriptor, Object> par : entrada.getAllFields().entrySet()) {
            FieldDescriptor campo = par.getKey();
            Object valor = par.getValue();
            if (campo.getJavaType() == FieldDescriptor.JavaType.MESSAGE) {
                Message interno = (Message) valor;
                String tipo = interno.getDescriptorForType().getName();
                if (tipo.equals("ListaTexto") || tipo.equals("ListaInteiros")) {
                    FieldDescriptor valores = interno.getDescriptorForType().findFieldByName("valores");
                    valor = new ArrayList<>((List<?>) interno.getField(valores));
                } else {
                    valor = Json.ler(imprimir(interno));
                }
            }
            resultado.put(campo.getJsonName(), valor);
        }
        return resultado;
    }

    private static String imprimir(Message mensagem) {
        try {
            return IMPRESSORA.print(mensagem);
        } catch (InvalidProtocolBufferException erro) {
            throw new IllegalStateException(erro);
        }
    }

    @SuppressWarnings("unchecked")
    static <M extends Message> M mensagem(Object dados, Message.Builder construtor) {
        try {
            LEITOR.merge(Json.escrever(dados), construtor);
        } catch (InvalidProtocolBufferException erro) {
            throw new IllegalStateException(erro);
        }
        return (M) construtor.build();
    }

    static Map<String, Object> pagina(Pagina origem) {
        Map<String, Object> resultado = new LinkedHashMap<>();
        resultado.put("itens", origem.itens());
        resultado.put("pagina", origem.pagina());
        resultado.put("tamanho", origem.tamanho());
        resultado.put("total", origem.total());
        return resultado;
    }

    static <M extends Message> M listar(Recurso recurso, ListarRequisicao requisicao, Message.Builder construtor) {
        Pagina pagina = recurso.listar(
                requisicao.hasPagina() ? requisicao.getPagina() : null,
                requisicao.hasTamanho() ? requisicao.getTamanho() : null,
                requisicao.hasNome() ? requisicao.getNome() : null);
        return mensagem(pagina(pagina), construtor);
    }

    static <M extends Message> M relacionados(Relacionados busca, ListarRelacionadosRequisicao requisicao,
            Message.Builder construtor) {
        Pagina pagina = busca.buscar(
                requisicao.getId(),
                requisicao.hasPagina() ? requisicao.getPagina() : null,
                requisicao.hasTamanho() ? requisicao.getTamanho() : null);
        return mensagem(pagina(pagina), construtor);
    }

    static <T> void responder(StreamObserver<T> saida, Supplier<T> acao) {
        T resposta;
        try {
            resposta = acao.get();
        } catch (NaoEncontrado erro) {
            saida.onError(Status.NOT_FOUND.withDescription(erro.getMessage()).asRuntimeException());
            return;
        } catch (Invalido erro) {
            saida.onError(Status.INVALID_ARGUMENT.withDescription(erro.getMessage()).asRuntimeException());
            return;
        } catch (Conflito erro) {
            saida.onError(Status.FAILED_PRECONDITION.withDescription(erro.getMessage()).asRuntimeException());
            return;
        } catch (RuntimeException erro) {
            saida.onError(Status.INTERNAL.withDescription(String.valueOf(erro.getMessage())).asRuntimeException());
            return;
        }
        saida.onNext(resposta);
        saida.onCompleted();
    }
}