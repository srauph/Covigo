$(document).ready(function () {

    const convertTime12to24 = (time12h) => {
        const [time, modifier] = time12h.split(' ');
        let [hours, minutes] = time.split(':');

        if (hours === '12') {
            hours = '00';
        }

        if (modifier === 'PM') {
            hours = parseInt(hours, 10) + 12;
        }

        return `${hours}:${minutes}`;
    }

    $('.timepicker_1').timepicker({
        timeFormat: 'h:mm p',
        interval: 15,
        defaultTime: '8:00',
        startTime: '8:00',
        dropdown: true,
        scrollbar: true,
        change: function(){
            validateStartEndTime();
            validateSlotDuration();
        }
    });

    $('.timepicker_2').timepicker({
        timeFormat: 'h:mm p',
        interval: 15,
        defaultTime: '9:00',
        startTime: '8:00',
        dropdown: true,
        scrollbar: true,
        change: function(){
            validateStartEndTime();
            validateSlotDuration();
        }
    });

    $('#id_slot_duration_hours').change(function(){
        validateSlotDuration();
    });

    $('#id_slot_duration_minutes').change(function(){
        validateSlotDuration();
    });


    function validateStartEndTime() {
        let startTime = $('#start_time').val();
        let endTime = $('#end_time').val();

        let startTime24 = convertTime12to24(startTime);
        let endTime24 = convertTime12to24(endTime);

        // Need this check because endTime is not defined properly upon opening the page
        if (!String(startTime24).includes('undefined') && !String(endTime24).includes('undefined')) {
            let startTimeDate = new Date(new Date().toDateString() + ' ' + startTime24);
            let endTimeDate = new Date(new Date().toDateString() + ' ' + endTime24);

            let isValidTime = (startTimeDate < endTimeDate);

            if (!isValidTime) {
                $('#time-error').removeClass('hidden');
            } else {
                $('#time-error').addClass('hidden');
            }
            return isValidTime;
        }
        return false;

    }

    function validateSlotDuration() {
        //get the difference between end and start time
        //if slot duration is > than difference, error message
        let slotHours = $('#id_slot_duration_hours').val();
        let slotMinutes = $('#id_slot_duration_minutes').val();
        let slotDurationMinutes = parseInt(slotHours)*60 + parseInt(slotMinutes);

        const MILLIS_PER_MINUTE = 60000;

        if (validateStartEndTime()){
            let startTimeDate = new Date(new Date().toDateString() + ' ' + convertTime12to24($('#start_time').val()));
            let endTimeDate = new Date(new Date().toDateString() + ' ' + convertTime12to24($('#end_time').val()));
            const diffTime = Math.abs(endTimeDate - startTimeDate)/MILLIS_PER_MINUTE;

            if (slotDurationMinutes > diffTime){
                $('#slot-error').removeClass('hidden');
            }
            else{
                $('#slot-error').addClass('hidden');
            }
        }
    }

});