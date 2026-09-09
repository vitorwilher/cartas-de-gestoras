<?php
/**
 * CAPTURA "Cartas de Gestoras" -> ConvertKit.
 *
 * Grava nome, e-mail e telefone do formulario Elementor no Kit e aplica a tag
 * Mercado Financeiro (22406993).
 *
 * POR QUE ESTE SNIPPET EXISTE: a acao "ConvertKit" do Elementor Pro escreve
 * APENAS email e first_name. Ela LE as tags do Kit para montar o seletor, mas
 * nao ESCREVE campo nem tag a partir do formulario — verificado no payload real
 * e documentado no ROI_Diagnostico (3 plugins testados em 02-03/09/2026, todos
 * iguais). Sem esta ponte, o telefone simplesmente nao chega.
 *
 * ⚠️ scope DEVE ser "global" no Code Snippets. O submit do Elementor vai por
 *    admin-ajax.php, que NAO e coberto por "front-end". A ponte fica ativa, sem
 *    erro de sintaxe, e nao executa. Foi o que mais custou tempo no conserto de
 *    15/08 — se o dado parar de chegar, confira o ESCOPO antes do codigo.
 *
 * ⚠️ O Kit DESCARTA EM SILENCIO valor de campo que nao existe. Os campos usados
 *    aqui foram conferidos na API em 09/09/2026: phone (676333) e whatsapp
 *    (1142293). Se criar campo novo, crie ANTES no painel do Kit.
 *
 * ⚠️ /v3/tags/{id}/subscribe cria o assinante se ele nao existir E aplica a tag
 *    numa unica chamada — por isso nao dependemos da acao ConvertKit do
 *    Elementor. Se ela estiver ativa no form, nao ha problema: o Kit resolve por
 *    e-mail e nao duplica.
 *
 * FALHA ABERTA DE PROPOSITO: erro aqui nunca interrompe o cadastro. Assinante
 * sem telefone e muito melhor que assinante perdido.
 */

add_action( 'elementor_pro/forms/new_record', function ( $record, $handler ) {

	// Só este formulário. Defina "cartasgestoras" no Elementor em
	// Configurações Adicionais -> ID do formulário.
	$form_id   = $record->get_form_settings( 'form_id' );
	$form_name = $record->get_form_settings( 'form_name' );
	if ( 'cartasgestoras' !== $form_id && 'cartasgestoras' !== $form_name ) {
		return;
	}

	$TAG_MERCADO_FINANCEIRO = 22406993;   // conferida na API em 09/09/2026
	$secret = '<<<API_SECRET_DO_CONVERTKIT>>>';

	$fields = $record->get( 'fields' );
	$email = $nome = $telefone = '';

	foreach ( $fields as $id => $field ) {
		$valor = trim( (string) ( isset( $field['value'] ) ? $field['value'] : '' ) );
		if ( '' === $valor ) {
			continue;
		}
		$tipo = isset( $field['type'] ) ? $field['type'] : '';

		// Casamos por TIPO primeiro (robusto a renomear o campo) e por id depois.
		if ( 'email' === $tipo || 'email' === $id ) {
			$email = $valor;
		} elseif ( 'tel' === $tipo || 'telefone' === $id || 'phone' === $id ) {
			$telefone = $valor;
		} elseif ( 'nome' === $id || 'name' === $id || 'first_name' === $id ) {
			$nome = $valor;
		}
	}

	if ( '' === $email ) {
		error_log( '[CARTAS->CK] submit sem e-mail; nada a fazer.' );
		return;
	}

	// Normaliza o telefone para dígitos e acrescenta o DDI do Brasil quando o
	// número vier só com DDD — é o formato que o disparo de WhatsApp espera.
	$digitos = preg_replace( '/\D+/', '', $telefone );
	if ( '' !== $digitos && strlen( $digitos ) <= 11 ) {
		$digitos = '55' . $digitos;
	}

	$campos = array();
	if ( '' !== $digitos ) {
		$campos['phone']    = $digitos;
		$campos['whatsapp'] = $digitos;   // a AM fecha venda por WhatsApp
	}

	$corpo = array(
		'api_secret' => $secret,
		'email'      => $email,
	);
	if ( '' !== $nome ) {
		$corpo['first_name'] = $nome;
	}
	if ( ! empty( $campos ) ) {
		$corpo['fields'] = $campos;
	}

	// Uma chamada só: cria o assinante (se preciso) e aplica a tag.
	$resp = wp_remote_post(
		'https://api.convertkit.com/v3/tags/' . $TAG_MERCADO_FINANCEIRO . '/subscribe',
		array(
			'timeout' => 20,
			'headers' => array( 'Content-Type' => 'application/json' ),
			'body'    => wp_json_encode( $corpo ),
		)
	);

	if ( is_wp_error( $resp ) ) {
		error_log( '[CARTAS->CK] falhou: ' . $resp->get_error_message() );
		return;
	}

	$code = wp_remote_retrieve_response_code( $resp );
	if ( $code >= 200 && $code < 300 ) {
		error_log( sprintf( '[CARTAS->CK] %s ok (telefone: %s)', $email,
			'' !== $digitos ? 'sim' : 'nao' ) );
	} else {
		error_log( sprintf( '[CARTAS->CK] %s HTTP %d: %s', $email, $code,
			substr( wp_remote_retrieve_body( $resp ), 0, 200 ) ) );
	}

}, 30, 2 );   // prioridade 30: depois da acao ConvertKit e da ponte de UTM (20)
