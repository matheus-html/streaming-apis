package streaming.gql;

import graphql.scalars.ExtendedScalars;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.graphql.execution.RuntimeWiringConfigurer;

@Configuration
public class ConfiguracaoGraphql {

    @Bean
    public RuntimeWiringConfigurer escalares() {
        return construtor -> construtor.scalar(ExtendedScalars.Json);
    }
}