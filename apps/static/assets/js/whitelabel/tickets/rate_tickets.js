function attachRatingEventListeners() {
    var selectedRating = 0;
    var ticketId = 0;
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Mostrar modal al hacer clic en el botón de calificación
    $(document).on('click', '.rate-ticket-btn', function() {
        ticketId = $(this).data('ticket-id');
        var currentRating = $(this).data('ticket-rating');

        selectedRating = currentRating || 0;
        highlightStars(selectedRating); // Resaltar estrellas con la calificación actual

        if (currentRating && currentRating > 0) {
            // Si el ticket ya está calificado, deshabilitar las estrellas
            $('#rateModal .star').css('pointer-events', 'none');
            $('#submitRating').hide();
            $('#cancelRating').hide();
        } else {
            // Si el ticket no está calificado, habilitar las estrellas
            $('#rateModal .star').css('pointer-events', 'auto');
            $('#submitRating').show();
            $('#cancelRating').show();
        }

        $('#modalTicketId').text(ticketId); // Actualiza el título del modal con el ID del ticket
        $('#rateModal').modal('show');
    });

    // Manejar el hover de las estrellas
    $('.star').off('mouseover').on('mouseover', function() {
        var rating = $(this).data('value');
        highlightStars(rating);
    });

    // Manejar el mouseout de las estrellas
    $('.star').off('mouseout').on('mouseout', function() {
        highlightStars(selectedRating);
    });

    // Seleccionar estrella de calificación
    $('.star').off('click').on('click', function() {
        selectedRating = $(this).data('value');
        highlightStars(selectedRating);
    });

    // Función para resaltar estrellas
    function highlightStars(rating) {
        $('.star').each(function() {
            var starValue = $(this).data('value');
            $(this).removeClass('highlighted-red highlighted-orange highlighted-yellow highlighted-green'); // Eliminar clases anteriores

            if (starValue <= rating) {
                if (rating <= 2) {
                    $(this).addClass('highlighted-red'); // Siempre rojo para 1-2 estrellas
                } else if (rating == 3) {
                    $(this).addClass('highlighted-orange'); // Siempre naranja para 3 estrellas
                } else if (rating == 4) {
                    $(this).addClass('highlighted-yellow'); // Siempre amarillo para 4 estrellas
                } else if (rating == 5) {
                    $(this).addClass('highlighted-green'); // Siempre verde para 5 estrellas
                }
            }
        });
    }

    // Enviar calificación
    $('#submitRating').off('click').on('click', function() {
        if (selectedRating > 0) {
            $.ajax({
                url: '',
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken // Asegúrate de enviar el token CSRF en el encabezado
                },
                data: {
                    rate_ticket: true,
                    ticket_id: ticketId,
                    rating: selectedRating
                },
                success: function(response) {
                    if (response.success) {
                        $('#rateModal').modal('hide');
                        var btn = $('.rate-ticket-btn[data-ticket-id="' + ticketId + '"]');
                        btn.removeClass('btn-success').addClass('btn-secondary rate-ticket-btn rated')
                        .data('ticket-rating', selectedRating)
                        .removeClass('border-red border-orange border-yellow border-green');

                        // Añadir la clase de borde adecuada según la calificación
                        if (selectedRating <= 2) {
                            btn.addClass('border-red');
                        } else if (selectedRating == 3) {
                            btn.addClass('border-orange');
                        } else if (selectedRating == 4) {
                            btn.addClass('border-yellow');
                        } else {
                            btn.addClass('border-green');
                        }

                        btn.empty();  // Limpiar contenido del botón
                        var starsHtml = '<div class="stars">';
                        for (var i = 1; i <= 5; i++) {
                            var starClass = 'fa-solid fa-star star-rating';
                            if (i <= selectedRating) {
                                if (selectedRating <= 2) {
                                    starClass += ' red';
                                } else if (selectedRating == 3) {
                                    starClass += ' orange';
                                } else if (selectedRating == 4) {
                                    starClass += ' yellow';
                                } else if (selectedRating == 5) {
                                    starClass += ' green';
                                }
                            }
                            starsHtml += '<i class="' + starClass + '" data-rating="' + i + '"></i>';
                        }
                        starsHtml += '</div>';
                        btn.append(starsHtml);

                    } else {
                        alert('Failed to submit rating: ' + (response.error || 'Unknown error'));
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error submitting rating:', error, xhr.responseText);
                    alert('Failed to submit rating.');
                }
            });
        } else {
            alert('Please select a rating before submitting.');
        }
    });

    // Pintar estrellas según la calificación en los botones
    document.querySelectorAll('.rate-ticket-btn').forEach(function(button) {
        let rating = parseInt(button.getAttribute('data-ticket-rating'));

        // Añadir clase 'rated' solo si el botón está calificado
        if (rating > 0) {
            button.classList.add('rated');
            button.classList.remove('border-red', 'border-orange', 'border-yellow', 'border-green'); // Remover clases anteriores

            // Añadir la clase de borde adecuada según la calificación
            if (rating <= 2) {
                button.classList.add('border-red');
            } else if (rating == 3) {
                button.classList.add('border-orange');
            } else if (rating == 4) {
                button.classList.add('border-yellow');
            } else {
                button.classList.add('border-green');
            }
        } else {
            button.classList.remove('rated', 'border-red', 'border-orange', 'border-yellow', 'border-green');
        }

        let stars = button.querySelectorAll('.star-rating');
        stars.forEach(function(star, index) {
            star.classList.remove('red', 'orange', 'yellow', 'green'); // Remover clases anteriores

            if (index < rating) {
                if (rating <= 2) {
                    star.classList.add('red');
                } else if (rating == 3) {
                    star.classList.add('orange');
                } else if (rating == 4) {
                    star.classList.add('yellow');
                } else if (rating == 5) {
                    star.classList.add('green');
                }
            }
        });
    });

}

function createRatingButton(ticket) {
    if (ticket.status === "Closed" && ticket.user_created === 1) {
        if (ticket.rating) {
            return rateButtonTemplateSuccess
                .replace(/__ticketId__/g, ticket.id)
                .replace(/__ticketRating__/g, ticket.rating);
        } else {
            return rateButtonTemplateSecondary
                .replace(/__ticketId__/g, ticket.id)
                .replace(/__ticketRating__/g, '');
        }
    }
    return '';
}

function openRatingModal(ticketId) {
    document.getElementById('modalTicketId').textContent = ticketId;
    var rateModal = new bootstrap.Modal(document.getElementById('rateModal'));
    rateModal.show();
}

function highlightStars(rating) {
    $('.star').each(function() {
        var starValue = $(this).data('value');
        if (starValue <= rating) {
            $(this).addClass('highlighted');
        } else {
            $(this).removeClass('highlighted');
        }
    });
}

$(document).ready(function() {
    attachRatingEventListeners(); // Aplicar los event listeners inicialmente
});
