package streaming.grpc;

import io.grpc.stub.StreamObserver;
import streaming.MusicaServiceGrpc;
import streaming.Streaming.IdRequisicao;
import streaming.Streaming.ListarRelacionadosRequisicao;
import streaming.Streaming.ListarRequisicao;
import streaming.Streaming.Musica;
import streaming.Streaming.MusicaAtualizacao;
import streaming.Streaming.MusicaEntrada;
import streaming.Streaming.PaginaMusicas;
import streaming.Streaming.PaginaPlaylists;
import streaming.Streaming.Vazio;
import streaming.core.Servicos;

public final class MusicaServico extends MusicaServiceGrpc.MusicaServiceImplBase {

    @Override
    public void listar(ListarRequisicao requisicao, StreamObserver<PaginaMusicas> saida) {
        Ponte.responder(saida, () -> Ponte.listar(Servicos.MUSICAS, requisicao, PaginaMusicas.newBuilder()));
    }

    @Override
    public void obter(IdRequisicao requisicao, StreamObserver<Musica> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(Servicos.MUSICAS.obter(requisicao.getId()),
                Musica.newBuilder()));
    }

    @Override
    public void criar(MusicaEntrada requisicao, StreamObserver<Musica> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(Servicos.MUSICAS.criar(Ponte.dados(requisicao)),
                Musica.newBuilder()));
    }

    @Override
    public void atualizar(MusicaAtualizacao requisicao, StreamObserver<Musica> saida) {
        Ponte.responder(saida, () -> Ponte.mensagem(
                Servicos.MUSICAS.atualizar(requisicao.getId(), Ponte.dados(requisicao.getEntrada())),
                Musica.newBuilder()));
    }

    @Override
    public void remover(IdRequisicao requisicao, StreamObserver<Vazio> saida) {
        Ponte.responder(saida, () -> {
            Servicos.MUSICAS.remover(requisicao.getId());
            return Vazio.getDefaultInstance();
        });
    }

    @Override
    public void listarPlaylists(ListarRelacionadosRequisicao requisicao, StreamObserver<PaginaPlaylists> saida) {
        Ponte.responder(saida, () -> Ponte.relacionados(Servicos::playlistsDaMusica, requisicao,
                PaginaPlaylists.newBuilder()));
    }
}