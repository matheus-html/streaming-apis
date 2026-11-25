package streaming.grpc;

import io.grpc.stub.StreamObserver;
import streaming.PlaylistServiceGrpc;
import streaming.Streaming.IdRequisicao;
import streaming.Streaming.ListarRelacionadosRequisicao;
import streaming.Streaming.ListarRequisicao;
import streaming.Streaming.PaginaMusicas;
import streaming.Streaming.PaginaPlaylists;
import streaming.Streaming.Playlist;
import streaming.Streaming.PlaylistAtualizacao;
import streaming.Streaming.PlaylistEntrada;
import streaming.Streaming.Vazio;
import streaming.core.Servicos;

public final class PlaylistServico extends PlaylistServiceGrpc.PlaylistServiceImplBase {

    @Override
    public void listar(ListarRequisicao requisicao, StreamObserver<PaginaPlaylists> saida) {
        Ponte.responder(saida, () -> Ponte.listar(Servicos.PLAYLISTS, requisicao, PaginaPlaylists.newBuilder()));
    }

    @Override
    public void obter(IdRequisicao requisicao, StreamObserver<Playlist> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(Servicos.PLAYLISTS.obter(requisicao.getId()),
                Playlist.newBuilder()));
    }

    @Override
    public void criar(PlaylistEntrada requisicao, StreamObserver<Playlist> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(Servicos.PLAYLISTS.criar(Ponte.dados(requisicao)),
                Playlist.newBuilder()));
    }

    @Override
    public void atualizar(PlaylistAtualizacao requisicao, StreamObserver<Playlist> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(
                Servicos.PLAYLISTS.atualizar(requisicao.getId(), Ponte.dados(requisicao.getEntrada())),
                Playlist.newBuilder()));
    }

    @Override
    public void remover(IdRequisicao requisicao, StreamObserver<Vazio> saida) {
        Ponte.responder(saida, () -> {
            Servicos.PLAYLISTS.remover(requisicao.getId());
            return Vazio.getDefaultInstance();
        });
    }

    @Override
    public void listarMusicas(ListarRelacionadosRequisicao requisicao, StreamObserver<PaginaMusicas> saida) {
        Ponte.responder(saida, () -> Ponte.relacionados(Servicos::musicasDaPlaylist, requisicao,
                PaginaMusicas.newBuilder()));
    }
}