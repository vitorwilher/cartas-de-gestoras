<?php
/**
 * CAPTURA "Cartas de Gestoras" -> ConvertKit (sequencia 2888305).
 *
 * Grava nome, e-mail e telefone e INSCREVE NA MESMA SEQUENCIA que a landing
 * nativa do Kit dispara (a que o Alan montou em
 * /sintese-semanal-das-cartas-das-gestoras). Assim as duas portas de entrada
 * entregam a mesma regua de e-mail, e a metrica nao se parte.
 *
 * POR QUE ESTE SNIPPET EXISTE: a acao "ConvertKit" do Elementor Pro escreve
 * APENAS email e first_name. Ela LE as tags do Kit para montar o seletor, mas
 * nao ESCREVE campo, tag nem sequencia a partir do formulario. Verificado no
 * payload real e documentado no ROI_Diagnostico (3 plugins testados em
 * 02-03/09/2026, todos iguais). Sem esta ponte, o telefone nao chega.
 *
 * ⚠️ scope DEVE ser "global" no Code Snippets. O submit do Elementor vai por
 *    admin-ajax.php, que NAO e coberto por "front-end". A ponte fica ativa, sem
 *    erro de sintaxe, e nao executa. Foi o que mais custou tempo no conserto de
 *    15/08 — se o dado parar de chegar, confira o ESCOPO antes do codigo.
 *
 * ⚠️ O Kit DESCARTA EM SILENCIO valor de campo que nao existe. Os campos aqui
 *    foram conferidos na API em 09/09/2026: phone (676333) e whatsapp (1142293).
 *
 * ⚠️ NAO enviamos WhatsApp a partir daqui. A Meta so permite mensagem fora da
 *    janela de 24h por template aprovado para AQUELE uso, e usar o template
 *    UTILITY de entrega do PDF para captacao e reclassificacao de uso — que a
 *    Meta descarta em silencio (a API responde "accepted") e ainda derruba a
 *    qualidade do numero de producao. A pagina de obrigado pede que o LEAD mande
 *    "Oi", e e o lead que abre a janela. Ver README.md.
 *
 * FALHA ABERTA DE PROPOSITO: erro aqui nunca interrompe o cadastro. Assinante
 * sem telefone e muito melhor que assinante perdido.
 */

add_action( 'elementor_pro/forms/new_record', function ( $record, $handler ) {

	// Só este formulário. Definir "cartasgestoras" no Elementor em
	// Configurações Adicionais -> ID do formulário.
	$form_id   = $record->get_form_settings( 'form_id' );
	$form_name = $record->get_form_settings( 'form_name' );
	if ( 'cartasgestoras' !== $form_id && 'cartasgestoras' !== $form_name ) {
		return;
	}

	// Conferidos na API do Kit em 09/09/2026.
	$SEQUENCIA = 2888305;    // "Cartas Semanais: Síntese Semanal das Cartas das Gestoras"

	// TRÊS tags, com papéis diferentes:
	//   - PROJETO identifica quem veio DESTA landing. É a ÚNICA que a automação
	//     de WhatsApp consulta para decidir se responde com o PDF.
	//   - As outras duas alimentam segmentação e broadcast: uma pelo tema
	//     (Mercado Financeiro, 534 pessoas) e outra pelo formato (Exercícios).
	// Usar uma guarda-chuva como critério de envio mandaria PDF para gente que
	// nunca ouviu falar deste projeto.
	$TAG_PROJETO = 23251247;   // "Leads - Cartas Semanais"  ← decide o envio
	$TAGS_TEMA   = array(
		22406993,   // "Mercado Financeiro"
		13265211,   // "Leads - Exercícios"
	);
	$secret    = '<<<API_SECRET_DO_CONVERTKIT>>>';

	$fields = $record->get( 'fields' );
	$email = $nome = $telefone = '';

	foreach ( $fields as $id => $field ) {
		$valor = trim( (string) ( isset( $field['value'] ) ? $field['value'] : '' ) );
		if ( '' === $valor ) {
			continue;
		}
		$tipo = isset( $field['type'] ) ? $field['type'] : '';

		// Casa por TIPO primeiro (robusto a renomear o campo), por id depois.
		if ( 'email' === $tipo || 'email' === $id ) {
			$email = $valor;
		} elseif ( 'tel' === $tipo || 'telefone' === $id || 'whatsapp' === $id ) {
			$telefone = $valor;
		} elseif ( 'nome' === $id || 'name' === $id || 'first_name' === $id ) {
			$nome = $valor;
		}
	}

	if ( '' === $email ) {
		error_log( '[CARTAS->CK] submit sem e-mail; nada a fazer.' );
		return;
	}

	// Normaliza para dígitos e acrescenta o DDI quando vem só com DDD — é o
	// formato que o disparo de WhatsApp espera quando a janela estiver aberta.
	$digitos = preg_replace( '/\D+/', '', $telefone );
	if ( '' !== $digitos && strlen( $digitos ) <= 11 ) {
		$digitos = '55' . $digitos;
	}

	$corpo = array( 'api_secret' => $secret, 'email' => $email );
	if ( '' !== $nome ) {
		$corpo['first_name'] = $nome;
	}
	if ( '' !== $digitos ) {
		$corpo['fields'] = array( 'phone' => $digitos, 'whatsapp' => $digitos );
	}

	// Uma chamada: cria o assinante, grava os campos e inicia a sequência.
	$resp = wp_remote_post(
		'https://api.convertkit.com/v3/sequences/' . $SEQUENCIA . '/subscribe',
		array(
			'timeout' => 20,
			'headers' => array( 'Content-Type' => 'application/json' ),
			'body'    => wp_json_encode( $corpo ),
		)
	);

	if ( is_wp_error( $resp ) ) {
		error_log( '[CARTAS->CK] sequência falhou: ' . $resp->get_error_message() );
	} else {
		$code = wp_remote_retrieve_response_code( $resp );
		error_log( sprintf( '[CARTAS->CK] %s sequência HTTP %d (telefone: %s)',
			$email, $code, '' !== $digitos ? 'sim' : 'nao' ) );
	}

	// As tags são separadas da sequência: a sequência entrega a régua de e-mail,
	// as tags segmentam. Falha em uma não impede a outra.
	foreach ( array_merge( array( $TAG_PROJETO ), $TAGS_TEMA ) as $tag_id ) {
		$r = wp_remote_post(
			'https://api.convertkit.com/v3/tags/' . $tag_id . '/subscribe',
			array(
				'timeout' => 20,
				'headers' => array( 'Content-Type' => 'application/json' ),
				'body'    => wp_json_encode( array( 'api_secret' => $secret, 'email' => $email ) ),
			)
		);
		if ( is_wp_error( $r ) ) {
			error_log( '[CARTAS->CK] tag ' . $tag_id . ' falhou: ' . $r->get_error_message() );
		}
	}

}, 40, 2 );   // prioridade 40: depois da ponte de UTM (20) e das Categorias (30).
              // Nao usar 30: o snippet id 10 ja ocupa, e prioridade igual deixa a
              // ordem indefinida. Sao formularios diferentes, entao seria inofensivo,
              // mas ordem definida e mais facil de depurar depois.
