package streaming.grpc;

import io.grpc.stub.StreamObserver;
import streaming.Streaming.IdRequisicao;
import streaming.Streaming.ListarRelacionadosRequisicao;
import streaming.Streaming.ListarRequisicao;
import streaming.Streaming.PaginaPlaylists;
import streaming.Streaming.PaginaUsuarios;
import streaming.Streaming.Usuario;
import streaming.Streaming.UsuarioAtualizacao;
import streaming.Streaming.UsuarioEntrada;
import streaming.Streaming.Vazio;
import streaming.UsuarioServiceGrpc;
import streaming.core.Servicos;

public final class UsuarioServico extends UsuarioServiceGrpc.UsuarioServiceImplBase {

    @Override
    public void listar(ListarRequisicao requisicao, StreamObserver<PaginaUsuarios> saida) {
        Ponte.responder(saida, () -> Ponte.listar(Servicos.USUARIOS, requisicao, PaginaUsuarios.newBuilder()));
    }

    @Override
    public void obter(IdRequisicao requisicao, StreamObserver<Usuario> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(Servicos.USUARIOS.obter(requisicao.getId()),
                Usuario.newBuilder()));
    }

    @Override
    public void criar(UsuarioEntrada requisicao, StreamObserver<Usuario> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(Servicos.USUARIOS.criar(Ponte.dados(requisicao)),
                Usuario.newBuilder()));
    }

    @Override
    public void atualizar(UsuarioAtualizacao requisicao, StreamObserver<Usuario> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(
                Servicos.USUARIOS.atualizar(requisicao.getId(), Ponte.dados(requisicao.getEntrada())),
                Usuario.newBuilder()));
    }

    @Override
    public void remover(IdRequisicao requisicao, StreamObserver<Vazio> saida) {
        Ponte.responder(saida, () -> {
            Servicos.USUARIOS.remover(requisicao.getId());
            return Vazio.getDefaultInstance();
        });
    }

    @Override
    public void listarPlaylists(ListarRelacionadosRequisicao requisicao, StreamObserver<PaginaPlaylists> saida) {
        Ponte.responder(saida, () -> Ponte.relacionados(Servicos::playlistsDoUsuario, requisicao,
                PaginaPlaylists.newBuilder()));
    }
}