function ajaxgetcollege(ths) {
	var college = $(ths).val();
	$.ajax({
		type: 'GET',
		url: '/AjaxGetMajor',
		dataType: 'json',
		data: {"select_college": college},
		success: function (ret) {
			//查询成功之后填充select option
			var html = "";
			html += "<option value=''>" + "---专业---" + "</option>";
			//用for循环遍历返回结果
			for(var i = 0; i < ret.length; i++) {
				var iteam = ret[i];
				var major = iteam.major_id__major_name;
				html += "<option value=" + major + ">" + major + "</option>";
			}
			$("#major_name").html(html);
			//将新数据填充到option
		}
	});
}
function ajaxgetmajor(ths) {
	var major = $(ths).val();
	$.ajax({
		type: 'GET',
		url: '/AjaxGetGrade',
		dataType: 'json',
		data: {"select_major": major},
		success: function (ret) {
			//查询成功之后填充select option
			var html = "";
			html += "<option value=''>" + "---班级---" + "</option>";
			//用for循环遍历返回结果
			for(var i = 0; i < ret.length; i++) {
				var iteam = ret[i];
				var grade = iteam.grade_id__grade_name;
				html += "<option value=" + grade + ">" + grade + "</option>";
			}
			$("#grade_name").html(html);
			//将新数据填充到option
		}
	});
}