package streaming.gql;

import graphql.GraphQLError;
import graphql.GraphqlErrorBuilder;
import graphql.schema.DataFetchingEnvironment;
import java.util.Map;
import org.springframework.graphql.execution.DataFetcherExceptionResolverAdapter;
import org.springframework.stereotype.Component;
import streaming.core.Conflito;
import streaming.core.Invalido;
import streaming.core.NaoEncontrado;

@Component
public class ResolvedorErros extends DataFetcherExceptionResolverAdapter {

    @Override
    protected GraphQLError resolveToSingleError(Throwable erro, DataFetchingEnvironment ambiente) {
        String codigo;
        if (erro instanceof NaoEncontrado) {
            codigo = "NAO_ENCONTRADO";
        } else if (erro instanceof Invalido) {
            codigo = "ENTRADA_INVALIDA";
        } else if (erro instanceof Conflito) {
            codigo = "CONFLITO";
        } else {
            return null;
        }
        return GraphqlErrorBuilder.newError(ambiente)
                .message(erro.getMessage())
                .extensions(Map.<String, Object>of("codigo", codigo))
                .build();
    }
}